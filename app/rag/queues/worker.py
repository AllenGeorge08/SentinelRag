import logging
import os
import re
import signal
from typing import Any
from urllib.parse import urlparse

from dotenv import load_dotenv
from langsmith import traceable
from openrouter import OpenRouter
from qdrant_client.models import models

from app.evaluation.metrics.llm_client import generation_model
from app.rag.clients.qdrant_client import client
from app.rag.config.config import (
    COLLECTION_NAME,
    dense_embedding_model,
    sparse_embedding_model,
)

import asyncio
from bullmq import Job, Worker 

load_dotenv()

or_client = OpenRouter(api_key=os.environ["OPENROUTER_API_KEY"])
RERANK_MODEL = "cohere/rerank-5-fast"  # or "cohere/rerank-5-pro"
RERANK_MIN = None  
log = logging.getLogger(__name__)
QUEUE_NAME="SentinelRag"
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

SYSTEM_PROMPT = """You answer questions using ONLY the numbered context passages below.

Rules:
- Use only statements the passages explicitly make. Do not use prior knowledge.
- Do not describe a risk or claim unless a passage explains it. A name in a "see also" list is not an explanation.
- Cite passages inline like [1], [2].
- If the passages do not answer the question, reply exactly: "Not found in the documents."
- Do not write source, page, or suggestion lines. They are added automatically.

<context>
{context}
</context>"""

def build_redis_connection(url:str) -> dict[str,Any]:
    parsed = urlparse(url)
    conn: dict[str,Any] = {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 6379
    }
    if parsed.password:
        conn["password"] = parsed.password
    if parsed.path and parsed.path != "/":
        conn["db"] = int(parsed.path.lstrip("/"))
    return conn 


def retrieve(query: str, top_n: int = 5):
    res = client.query_points(
        COLLECTION_NAME,
        prefetch=[
            models.Prefetch(
                query=models.Document(text=query, model=dense_embedding_model),
                using="dense",
                limit=30,
            ),
            models.Prefetch(
                query=models.Document(text=query, model=sparse_embedding_model),
                using="sparse",
                limit=30,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        with_payload=True,
        limit=30,
    )
    seen, pool = set(), []
    for p in res.points:
        key = "".join(p.payload["text"].split())[:200]
        if key not in seen:
            seen.add(key)
            pool.append(p.payload)
    try:
        rr = or_client.rerank.rerank(
            model=RERANK_MODEL,
            query=query,
            documents=[f"{pl['title']}\n{pl['text']}" for pl in pool],
            top_n=top_n,
        )
        return [
            {**pool[r.index], "rerank_score": r.relevance_score, "reranked": True}
            for r in rr.results
        ]
    except Exception as e:  # keep eval runs alive, but make fallbacks visible
        log.warning("rerank failed, falling back to RRF order: %s", e)
        return [{**pl, "rerank_score": None, "reranked": False} for pl in pool[:top_n]]


def build_context(chunks) -> str:
    return "\n\n".join(
        f"[{i}] {c['title']} (PDF p.{c['page']})\n{c['text']}"
        for i, c in enumerate(chunks, 1)
    )


def build_footer(answer: str, chunks) -> str:
    cited = {int(n) for n in re.findall(r"\[(\d+)\]", answer)}
    used = [c for i, c in enumerate(chunks, 1) if i in cited] or chunks
    seen, lines = set(), []
    for c in used:
        k = (c["title"], c["page"])
        if k not in seen:
            seen.add(k)
            lines.append(f"- {c['title']}, PDF p.{c['page']}")
    return "Sources:\n" + "\n".join(lines)


@traceable
async  def process_query(user_query: str,job: Job|None = None):
    if job:
        await job.updateProgress({"stage":"retrieving"})

    # Offload synchronous retrieval
    
    chunks = await asyncio.to_thread(retrieve,user_query)

    # optional: refuse without calling the LLM when retrieval is weak
    if RERANK_MIN is not None and (
        not chunks or (chunks[0]["rerank_score"] or 0) < RERANK_MIN
    ):
        return {
            "answer": "Not found in the documents.",
            "formatted_answer": "Not found in the documents.",
            "contexts": [],
            "documents": [],
        }

    if job:
        await job.updateProgress({"stage": "generating"})

    response = generation_model.invoke(
        [
            {
                "role": "system",
                "content": SYSTEM_PROMPT.format(context=build_context(chunks)),
            },
            {"role": "user", "content": user_query},
        ]
    )
    answer = (
        response.content if hasattr(response, "content") else str(response)
    ).strip()

    refused = answer.lower().startswith("not found in the documents")
    return {
        "answer": answer,  # judges read this
        "formatted_answer": answer
        if refused
        else f"{answer}\n\n{build_footer(answer, chunks)}",  # users read this
        "contexts": [c["text"] for c in chunks],  # exact chunks the generator saw
        "documents": chunks,  # plain dicts: text, page, source, title, rerank_score
    }


async def processor(job: Job, token: str) -> dict[str, Any]:
    # Match whatever key server.py puts into queue.add(...)
    user_query = job.data.get("query") or job.data.get("user_query")
    if not user_query or not isinstance(user_query, str):
        raise ValueError(f"Invalid query payload in job={job.id}: {job.data}")
    return await process_query(user_query=user_query, job=job)


async def main() -> None:
    worker = Worker(
        QUEUE_NAME,
        processor,
        {
            "connection": build_redis_connection(REDIS_URL),
            "concurrency": 4,
            "lockDuration": 90_000,
            "stalledInterval": 30_000,
        },
    )

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    log.info("Worker listening on queue=%s redis=%s", QUEUE_NAME, REDIS_URL)
    await stop_event.wait()

    log.info("Shutting down worker...")
    await worker.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())