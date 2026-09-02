from langsmith import Client
import pandas as pd 
import os 
from dotenv import load_dotenv
from typing_extensions import Annotated,TypedDict
from app.evaluation.metrics.answer_relevance import relevance
from app.evaluation.metrics.faithfulness import faithfulness
from app.evaluation.metrics.correctness import correctness
from app.evaluation.metrics.retrieval_relevance import retrieval_relevance
from app.rag.queues.worker import process_query
from pathlib import Path

#Creating dataset
load_dotenv()

LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
print("API Keys Configured Succesfully")

client = Client(api_key=LANGSMITH_API_KEY)

DATA_DIR = Path(__file__).parent

dataset_name = "AI Security RAG-BOT Evaluation"
dataset_main = pd.read_csv(DATA_DIR/"dataset.csv")

examples = []

for _,row in dataset_main.iterrows():
    examples.append({
        "inputs": {"question": row["question"]},
        "outputs": {"answer": row["answer"]},
    })


if client.has_dataset(dataset_name=dataset_name):
    client.delete_dataset(dataset_name=dataset_name)

dataset = client.create_dataset(dataset_name=dataset_name)

# print(dataset)

example = client.create_examples(
    dataset_id=dataset.id,
    examples= examples   
)


print("Evaluation Examples created succesfully")

def target(inputs: dict) -> dict:
    return process_query(inputs["question"])


evaluation_results = client.evaluate(
    target,
    data=dataset_name,
    evaluators=[correctness,faithfulness,relevance,retrieval_relevance],
    experiment_prefix="rag-doc-relevance",
    metadata={"version": "LCEL Context, gpt-4-0125-preview"},

)


df = evaluation_results.to_pandas()

