import logging
import os
import re

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

load_dotenv()

or_client = OpenRouter(api_key=os.environ["OPENROUTER_API_KEY"])
RERANK_MODEL = "cohere/rerank-5-fast"  # or "cohere/rerank-5-pro"
RERANK_MIN = None  
log = logging.getLogger(__name__)


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
def process_query(user_query: str):
    chunks = retrieve(user_query)

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
