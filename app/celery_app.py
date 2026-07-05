"""
Day 17: Celery configuration.

Celery is a distributed task queue. It lets us run scoring tasks
in the background across one or more worker processes, completely
decoupled from the FastAPI request/response cycle.

Why upgrade from FastAPI BackgroundTasks to Celery?
- BackgroundTasks runs in the same process as the API server
  (if the server restarts mid-batch, tasks are lost)
- Celery runs in a separate worker process
  (tasks survive server restarts, can scale to multiple workers)
- Celery + Redis gives task monitoring, retries, and priorities
  for free — BackgroundTasks gives you none of these

Broker: Redis (stores task messages)
Backend: Redis (stores task results/status)
"""

import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "calibr",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_transport_options={
        "visibility_timeout": 3600,
    },
    broker_connection_retry_on_startup=True,
)