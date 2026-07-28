from langchain_community.document_loaders import PyPDFLoader
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore

pdf_dir = Path(__file__).parent.parent / "data"

docs = []

for pdf in pdf_dir.glob("*.pdf"):
    loader = PyPDFLoader(str(pdf))

    for doc in loader.load():
        doc.metadata["source"] = pdf.name 
        docs.append(doc)


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=400
)

chunks = text_splitter.split_documents(documents=docs)

embeddings = OllamaEmbeddings(model="nomic-embed-text")

vector_store = QdrantVectorStore.from_documents(documents=chunks,embedding=embeddings,url="http://localhost:6333",collection_name="rag")
print("Indexing Phase over")