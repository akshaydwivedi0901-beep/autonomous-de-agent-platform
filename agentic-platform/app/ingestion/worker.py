import redis
import json
from app.core.config import settings
from app.ingestion.tasks import process_document

r = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)


def start_worker():

    print("Ingestion worker started")

    while True:

        task = r.blpop("document_queue")

        payload = json.loads(task[1])

        process_document(payload["file"])
