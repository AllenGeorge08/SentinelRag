from os import path
from uu import Error
from langchain_community.document_loaders import PyPDFLoader
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag.clients.qdrant_client import client 
import pymupdf
from rag.config.config import dense_embedding_model,sparse_embedding_model,late_interaction_embedding_model,COLLECTION_NAME
from qdrant_client.models import Document,PointStruct,Distance,VectorParams,models
import logging

pdf_dir = Path(__file__).parent.parent.parent / "data"


if client.collection_exists(collection_name=COLLECTION_NAME):
   print("Collection already exists")
else:
    client.create_collection(
        COLLECTION_NAME,
        vectors_config={
            "dense": models.VectorParams(
                size=384,
                distance=models.Distance.COSINE
            ),
            "multi": models.VectorParams(
                size=96,
                distance=models.Distance.COSINE,
                # multi_vector_config=models.MultiVectorConfig(
                #     comparator=models.MultiVectorComparator.MAX_SIM,
                # ),
                multivector_config=models.MultiVectorConfig(
                    comparator=models.MultiVectorComparator.MAX_SIM
                ),
                hnsw_config=models.HnswConfigDiff(m=0)  #Re-ranking doesn't allow hnsfw
            ),
        },
        sparse_vectors_config={
            "sparse": models.SparseVectorParams(modifier=models.Modifier.IDF)
        }
    )
    print(f"Collection {COLLECTION_NAME} created..")



def load_docs(path):
    docs = []
    
    for pdf in path.glob("*.pdf"):
        loader = PyPDFLoader(str(pdf))
    
        for doc in loader.load():
            doc.metadata["source"] = str(pdf)
            doc.metadata["filename"] = pdf.name
            docs.append(doc)

    return docs



def parse_pdf(pdf_path):
    doc = pymupdf.open(str(pdf_path))
    pages= []
    print("Docs loaded") 
    for page_num,page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                pages.append({"page":page_num+1,"text": text})
    doc.close()
    return pages


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=200
)

# chunks = text_splitter.split_documents(documents=docs)
def chunk_pdf(pages,source):
    for page in pages:
        chunks = text_splitter.split_text(page["text"])
        for i,chunk in enumerate(chunks):
            yield{
                "text": chunk,
                "page": page["page"],
                "chunk_id": i,
                "source": source 
            }


def chunk_all_pdfs(path):
    print("Chunking pdfs...")
    for pdf in path.glob("*.pdf"):
        pages = parse_pdf(pdf)
        yield from chunk_pdf(pages,source=pdf.name)
    print("Pdf's chunked succesfully")


def build_points(chunks,dense_model,sparse_model,late_model):
    for idx,chunk in enumerate(chunks):
        yield PointStruct(
            id=idx,
            vector={
                "dense": Document(text=chunk["text"],model=dense_model),
                "sparse": Document(text=chunk["text"],model=sparse_model),
                "multi": Document(text=chunk["text"],model=late_model)
            },
        )

    

chunks = list(chunk_all_pdfs(pdf_dir))
points = list(build_points(chunks,dense_embedding_model,sparse_embedding_model,late_interaction_embedding_model))

try:
    client.upload_points(collection_name=COLLECTION_NAME,points=points)
    print("Indexing phase over...")
except Exception as e:
    logging.critical(f"Indexing Error: {e}")


