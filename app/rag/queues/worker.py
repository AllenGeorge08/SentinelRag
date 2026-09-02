import os 
from groq import Groq 
from dotenv import load_dotenv
from app.rag.config.config import dense_embedding_model,sparse_embedding_model,COLLECTION_NAME
from langsmith import traceable
from app.rag.clients.qdrant_client import client 
from qdrant_client.models import models
from app.rag.config.config import COLLECTION_NAME

load_dotenv()

groq_client = Groq(
    api_key=os.environ.get('GROQ_API_KEY')
)

# v1
# reasoning_model = ChatOllama(
#     model="deepseek-r1:1.5b",
#     validate_model_on_init=True,
#     reasoning=True
# )


# v1
# embedding_model = OllamaEmbeddings(
#     model="nomic-embed-text:latest "
# )

# v1
# vector_store = QdrantVectorStore.from_existing_collection(
#     embedding=embedding_model,
#     url="http://localhost:6333",
#     collection_name="rag"
# )

@traceable
def process_query(user_query: str):
    prefetch = [
        models.Prefetch(
            query=models.Document(text=user_query,model=dense_embedding_model),
            using="dense",
            limit=20
        ),
        models.Prefetch(
            query=models.Document(text=user_query,model=sparse_embedding_model),
            using="sparse",
            limit=20
        ),
    ]


    results = client.query_points(
        COLLECTION_NAME,
        prefetch=prefetch,
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        with_payload=True,
        limit=10,
    )


    context = [f"Page Content: {point.payload.get('text')}" f"Page Number: {point.payload.get('page')}\n" f"Source: {point.payload.get('source')}\n" for point in results.points]

    SYSTEM_PROMPT = f"""
    You are an intelligent document assistant.

    Your task is to answer user questions strictly from the retrieved PDF context.


    Rules:
    - Use ONLY the information provided below.
    - Never use prior knowledge.
    - Never guess missing information.
    - If the context is insufficient, say so politely.
    - If the answer spans multiple pages, summarize the information naturally.
    - Always cite the relevant page number(s).
    - If appropriate, recommend opening those pages for additional details.


    Response Format:

    Answer:
    <answer>

    Source Document:
    - Source document

    Page:
    - Page X
    - Page Y
    

    Suggestion:
    For more details, please open page(s) X, Y in the document.

    Context: 
    {context}

    """

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user","content": user_query}
    ]

    response =  groq_client.chat.completions.create(
        messages=messages,
        model="openai/gpt-oss-20b"
    )
    print(f"🤖: {response.choices[0].message.content}")
    answer =  response.choices[0].message.content
    return {
        "answer": answer,
        "documents": results
    }

