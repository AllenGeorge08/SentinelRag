from redis import Redis
from bullmq import Queue
import os 
import asyncio

REDIS_CONNECTION = {
    "host": os.getenv("REDIS_HOST","localhost"),
    "port": int(os.getenv("REDIS_PORT","6379"))
}

queue = Queue("SentinelRag",{"connection": REDIS_CONNECTION})

# asyncio.run(queue.setGlobalRateLimit(duration_ms=60*60))
