import os 
# from langchain_ollama import ChatOllama
from langchain_qdrant import QdrantVectorStore
from langchain_ollama import OllamaEmbeddings
from groq import Groq 
from dotenv import load_dotenv
from langsmith import traceable

load_dotenv()

client = Groq(
    api_key=os.environ.get('GROQ_API_KEY')
)

# reasoning_model = ChatOllama(
#     model="deepseek-r1:1.5b",
#     validate_model_on_init=True,
#     reasoning=True
# )


embedding_model = OllamaEmbeddings(
    model="nomic-embed-text:latest "
)

vector_store = QdrantVectorStore.from_existing_collection(
    embedding=embedding_model,
    url="http://localhost:6333",
    collection_name="rag"
)

@traceable
def process_query(user_query: str):
    results = vector_store.similarity_search(user_query,k=5)

    context = [f"Page Content: {result.page_content} \n Page Number: {result.metadata['page_label']} \n File Location: {result.metadata['source']}" for result in results]

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

    Retrieved Context:
    {context}
    """

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user","content": user_query}
    ]

    response =  client.chat.completions.create(
        messages=messages,
        model="openai/gpt-oss-20b"
    )
    print(f"🤖: {response.choices[0].message.content}")
    answer =  response.choices[0].message.content
    return {
        "answer": answer,
        "documents": results
    }

