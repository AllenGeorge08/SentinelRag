from csv import Error
from qdrant_client import QdrantClient
from dotenv import load_dotenv
import os 
import logging

load_dotenv()

try:
    QDRANT_URL= os.getenv("QDRANT_CLUSTER_ENDPOINT")
    QDRANT_API_KEY=os.getenv("QDRANT_API_KEY")
    print("Qdrant API Keys Loaded....")
except:
    raise Error("Qdrant credentials not found")


try:
    client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    cloud_inference=True,
    )
    print("Qdrant client initialized..")
except Exception as e:
    logging.critical(f"Qdrant client initialization error: {e}")

