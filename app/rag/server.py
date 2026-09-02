from fastapi import FastAPI, Query
from .clients.ragqueue_client import queue
from app.rag.queues.worker import process_query
from langsmith import traceable

app = FastAPI()

@app.get('/')
def root():
    return {'status': "Server is up and running"}

@traceable
@app.post('/chat')
def chat(query: str= Query(...,description="The chat query of user")):
    job = queue.enqueue(process_query,query) #enqueuess the process query and pasess query as a fn in it
    return {"status":"queued","job_id": job.id}

@traceable
@app.get('/job-status')
def get_result(job_id: str=Query(...,description="Job Id")):
    job = queue.fetch_job(job_id=job_id)
    result = job.return_value()
    print("Job status: ", job.get_status())
    return result
