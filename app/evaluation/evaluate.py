from langsmith import Client
import pandas as pd 
import os 
from dotenv import load_dotenv
from typing_extensions import Annotated,TypedDict


#Creating dataset

load_dotenv()

LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
print("API Keys Configured Succesfully")

client = Client(api_key=LANGSMITH_API_KEY)


dataset_name = "AI Security RAG-BOT Evaluation"
dataset_main = pd.read_csv("dataset.csv")

examples = []

for _,row in dataset_main.iterrows():
    examples.append({
        "inputs": {"question": row["question"]},
        "outputs": {"answer": row["answer"]},
    })

dataset = client.read_dataset(dataset_name=dataset_name)
# print(dataset)

client.create_examples(
    dataset_id=dataset.id,
    examples= examples   
)

print("Evaluation Examples created succesfully")


