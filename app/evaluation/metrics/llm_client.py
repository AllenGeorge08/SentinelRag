import os 
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_model = ChatGroq(
    api_key=GROQ_API_KEY,
    model="openai/gpt-oss-20b"
)


from langchain_nvidia_ai_endpoints import ChatNVIDIA
import os  


load_dotenv()

try:
    API_KEY = os.getenv("NVIDIA_API_KEY")
    # print("Your Nvidia api key is : ",API_KEY)
except:
    API_KEY = input("Enter your NVIDIA API KEY")

nvidia_llm = ChatNVIDIA(model="nvidia/nemotron-3-ultra-550b-a55b",nvidia_api_key=API_KEY)


from langchain_ollama import ChatOllama

ollama_model = ChatOllama(
    model="minimax-m3:cloud",
    reasoning=True
)


