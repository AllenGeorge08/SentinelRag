from fastapi import FastAPI, Query
from .clients.bullmq_client import queue
from app.rag.queues.worker import process_query
from langsmith import traceable
from bullmq import Job 
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await queue.close()

app = FastAPI(lifespan=lifespan)

@app.get('/')
def root():
    return {'status': "Server is up and running"}

@traceable
@app.post('/chat',status_code=202)
async def chat(query: str= Query(...,description="The chat query of user")):
    # job = queue.enqueue(process_query,query) #enqueuess the process query and pasess query as a fn in it
    job = await queue.add(
        "process_query",
        {"query": query},
        {
            "attempts": 3,
            "backoff": {"type": "exponential","delay":1500},
            "removeOnComplete": {"age": 3600,"count":1000},
            "removeOnFail": {"age":24*3600,"count": 1000}
        }
    )
    return {"status":"queued","job_id": job.id}

@traceable
@app.get('/job-status')
async def get_result(job_id: str=Query(...,description="Job Id")):
    # job = queue.fetch_job(job_id=job_id)
    job = await Job.fromId(queue,job_id)
    if job is None:
        return {"status": "not_found","job_id":job_id}
    
    state = await job.getState()

    if state == "completed":
        return {
            "status": "completed",
            "job_id": job.id,
            "result": job.returnvalue
        }

    if state == "failed":
        return {
            "status": "failed",
            "job_id": job.id,
            "error": job.failedReason
        }

    return {
        "status": state,
        "job_id": job.id,
        "progress": job.progress
    }

