# SentinelRag Evaluation Suite — Change Log

Date: Fri Nov 13 2026
Scope: Evaluation pipeline (LLM-as-a-Judge metrics + evaluation driver)

## Run 3 — Metadata-Based Indexing (pre-run-3)

- Added metadata-aware filtering support to the ingestion pipeline using `app/data/sources.yaml`
- Each document chunk now carries publisher, year, doc_type, and source URL metadata
- Enables metadata-aware filtering during retrieval (future improvement listed in README)

## Run 4 — Model Change (run3 → run4)

- Changed the judge model between run3 and run4
- Reason: Run3 was hitting rate limit errors during evaluation; switched to a more resilient model configuration

## Run 5 — Fri Nov 13 2026

- Changed `max_concurrency` from 4 to 1 in `app/evaluation/evaluate.py`
- Reason: Concurrency was causing errors during evaluation runs; sequential processing (1 at a time) is more stable

## Run 6 — Generation Model Change (run5 → run6)

- Replaced Groq `openai/gpt-oss-20b` with OpenRouter `anthropic/claude-3-5-haiku-20241022` as the generation model in `worker.py`
- Renamed `groq_model`/`groq_structured` to `generation_model`/`generation_structured`
- Added `NVIDIARerank` (`nvidia/llama-nemotron-rerank-1b-v2`) with `RERANK_MIN` threshold for optional pre-refusal
- Added OpenRouter client (`or_client`) for Cohere reranking fallback

## Run 7 — Rerank Model Change (pre-run-7)

- Changed rerank model to Cohere `cohere/rerank-5-fast` via OpenRouter rerank API in `worker.py`
- Added `try/except` around rerank call: falls back to raw RRF order if reranking fails, keeping evaluation runs alive
- Status: **FAILED** — evaluation did not complete successfully

## Run 8 — Dedup + Cohere-5 Reranker

- Added document deduplication (by normalized text key) in `retrieve()`
- Switched reranker to Cohere `cohere/rerank-5-fast` via OpenRouter rerank API
- Metrics reported:
  - Retrieval Relevance: 1.00 / 1.00
  - Faithfulness: 0.63 / 1.00
  - Relevance: 0.95/1.00
  - Correctness: 0.42 / 1.00
- Latency improvements:
  - P50 latency: 4.37s (down from baseline 22.99s avg)
  - P99 latency: 6.26s (down from baseline 95.11s)

## Summary of Changes

| Area | Change | Rationale / Impact |
|------|--------|-------------------|
| Primary judge model | Replaced Ollama (`minimax-m3:cloud`) with OpenRouter (`openai/gpt-6-luna`) across all four metrics | More capable reasoning model for grading; improved metric averages |
| Retry policy | Added `.with_retry(retry_if_exception_type=(Exception,), wait_exponential_jitter=True, stop_after_attempt=4)` to the OpenRouter judge | Transient API failures no longer fail evaluations; jitter avoids thundering herd |
| Fallback chain | Removed Groq and NVIDIA fallbacks entirely — OpenRouter is now the sole judge model | Simpler, single-model grading path; consistent scoring |
| `groq_model` | Still initialized in `llm_client.py` but unused by metrics | Retained for potential future use / worker pipeline |
| Faithfulness metric | `grounded` field type changed from `str` to `bool` | Boolean output is cleaner for aggregation and averaging |
| Answer relevance | Added `InMemoryRateLimiter` (0.12 req/s) to respect Groq rate limits | Avoids rate-limit errors during batch evaluation |
| Evaluation driver | Dataset handling is now idempotent: reads existing LangSmith dataset, deletes stale examples, recreates them | No more destructive delete-and-recreate; safer re-runs |
| Evaluation driver | Added `max_concurrency=4` to `client.evaluate()` | Parallel evaluation runs reduce total wall-clock time |
| Benchmark dataset | Filled missing question text ("What is a denial of service attack") | Complete Q/A pairs for all 20 benchmark items |
| Worker answer extraction | `worker.py` now extracts `.content` from Groq `AIMessage` instead of returning the message object | Fixes type mismatch so evaluation receives a plain string answer |
| Config | Fixed embedding model name casing (`all-MiniLM-L6-v2` → `all-minilm-l6-v2`) | Matches Qdrant model registry naming |

## Metrics Files Simplified

All four LLM-as-a-Judge evaluators now follow the same pattern:

```
openrouter_structured = openrouter_model.with_structured_output(
    <MetricSchema>, method="json_schema", strict=True,
).with_retry(
    retry_if_exception_type=(Exception,),
    wait_exponential_jitter=True,
    stop_after_attempt=4
)

<MetricName>_llm = openrouter_structured
```

Files affected:
- `app/evaluation/metrics/llm_client.py`
- `app/evaluation/metrics/correctness.py`
- `app/evaluation/metrics/faithfulness.py`
- `app/evaluation/metrics/retrieval_relevance.py`
- `app/evaluation/metrics/answer_relevance.py`

## How to Run

```bash
make evaluate   # Runs the full LangSmith evaluation pipeline
```

Evaluation is integrated with LangSmith for trace-level analysis and experiment tracking.
