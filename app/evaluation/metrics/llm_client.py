import os 
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = ChatGroq(
    api_key=GROQ_API_KEY,
    model="openai/gpt-oss-20b"
)

