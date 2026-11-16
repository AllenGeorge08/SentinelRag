# SentinelRag — End-to-End Architecture Diagram

This diagram shows the complete RAG pipeline with databases, queue, router, and all retrieval stages.

```mermaid
flowchart TD
    %% ==================== USER & ROUTER LAYER ====================
    subgraph User["👤 User / Client"]
        U[("User Query")]
    end

    subgraph Router["🌐 API Router — FastAPI"]
        API[("/chat POST — enqueue job")]
        API2[("/job-status GET — poll result")]
    end

    %% ==================== QUEUE LAYER ====================
    subgraph Queue["📨 Queue Layer — BullMQ (Redis-backed)"]
        Q1[("BullMQ Queue<br/>job queue")]
        W1[("BullMQ Worker<br/>processes jobs")]
    end

    %% ==================== RETRIEVAL LAYER ====================
    subgraph Retrieval["🔍 Retrieval Pipeline"]
        D1[("Dense Retrieval<br/>Qdrant Cloud<br/>vector search")]
        B1[("BM25 Retrieval<br/>Qdrant Cloud<br/>lexical search")]
        RRF[("RRF Merge<br/>Reciprocal Rank<br/>Fusion")]
        DEDUP[("Deduplication<br/>normalized key")]
        RERANK[("Cohere Reranker<br/>Rerank 5 Fast<br/>via OpenRouter")]
        TOP5[("Top 5 Chunks<br/>precision filter")]
    end

    %% ==================== DATABASES ====================
    subgraph Databases["🗄️ Databases / Vector Store"]
        QD[("Qdrant Cloud<br/>dense + sparse vectors<br/>collection: Rag-Collection")]
        REDIS[("Redis<br/>BullMQ backing store<br/>job state")]
    end

    %% ==================== GENERATION LAYER ====================
    subgraph Generation["🧠 Generation — OpenRouter"]
        LLM[("LLM — Claude 3.5 Haiku<br/>grounded answer + citations")]
    end

    %% ==================== OBSERVABILITY ====================
    subgraph Observability["📊 Observability — LangSmith"]
        LS[("LangSmith<br/>tracing + evaluation<br/>metrics logging")]
    end

    %% ==================== CONNECTIONS ====================
    U --> API
    API --> Q1
    Q1 --> W1
    W1 --> D1
    W1 --> B1
    D1 --> QD
    B1 --> QD
    D1 --> RRF
    B1 --> RRF
    RRF --> DEDUP
    DEDUP --> RERANK
    RERANK --> TOP5
    TOP5 --> LLM
    LLM --> API2
    Q1 -.-> REDIS
    W1 -.-> REDIS
    API -.-> LS
    W1 -.-> LS
    LLM -.-> LS

    %% ==================== STYLING ====================
    classDef user fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef router fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef queue fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef retrieval fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef db fill:#ffebee,stroke:#b71c1c,stroke-width:2px
    classDef gen fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef obs fill:#eceff1,stroke:#263238,stroke-width:2px

    class U user
    class API,API2 router
    class Q1,W1 queue
    class D1,B1,RRF,DEDUP,RERANK,TOP5 retrieval
    class QD,REDIS db
    class LLM gen
    class LS obs

    linkStyle default stroke-width:2px,fill:none,stroke:#333
    linkStyle 9,10 stroke:#b71c1c,stroke-width:2px,stroke-dasharray: 5 5
    linkStyle 15,16 stroke:#263238,stroke-width:2px,stroke-dasharray: 5 5
```

## Diagram Components

| Component | Type | Purpose |
|-----------|------|---------|
| **FastAPI** | Router | API entry point; enqueues jobs and serves job-status polling |
| **BullMQ Queue** | Queue | Redis-backed job queue for asynchronous RAG execution |
| **BullMQ Worker** | Worker | Picks up jobs and runs the full retrieval + generation pipeline |
| **Dense Retrieval** | Retriever | Qdrant Cloud vector search — semantic matching |
| **BM25 Retrieval** | Retriever | Qdrant Cloud lexical search — exact term matching |
| **RRF Merge** | Fusion | Reciprocal Rank Fusion combining dense + BM25 rankings |
| **Deduplication** | Filter | Removes duplicate chunks by normalized text key |
| **Cohere Reranker** | Reranker | Cross-encoder precision re-ranking (top 5) |
| **Claude 3.5 Haiku** | LLM | Generates grounded answer with page citations via OpenRouter |
| **Qdrant Cloud** | Database | Vector store for dense + sparse embeddings |
| **Redis** | Database | BullMQ backing store for job state |
| **LangSmith** | Observability | Tracing, evaluation, and metric logging |
