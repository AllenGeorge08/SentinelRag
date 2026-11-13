import os 
from dotenv import load_dotenv

load_dotenv()

from langchain_openrouter import ChatOpenRouter
from tenacity import retry_if_exception_type, wait_exponential_jitter, stop_after_attempt


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_EVALUATION_KEY=os.getenv("OPENROUTER_EVALUATION_KEY")

# Judge model for evaluation metrics
openrouter_model = ChatOpenRouter(
    api_key=OPENROUTER_API_KEY,
    model="openai/gpt-6-luna",
    temperature=0
)

# Generation model for RAG pipeline (worker.py)
generation_model = ChatOpenRouter(
    api_key=OPENROUTER_EVALUATION_KEY,
    model="anthropic/claude-haiku-5.5",
    temperature=0
).with_retry(
    retry_if_exception_type=(Exception,),
    wait_exponential_jitter=True,
    stop_after_attempt=4
)
