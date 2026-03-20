from fastapi import APIRouter
import redis
import json
from app.core.config import settings

router = APIRouter()

r = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)


@router.post("/upload")
async def upload(file_path: str):

    payload = {"file": file_path}

    r.rpush("document_queue", json.dumps(payload))

    return {"status": "queued"}