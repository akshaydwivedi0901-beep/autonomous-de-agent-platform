import redis
import json
from app.core.config import settings


class RedisMemory:

    def __init__(self):

        self.client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )

    def get_history(self, session_id):

        data = self.client.get(session_id)

        if not data:
            return []

        return json.loads(data)

    def save_history(self, session_id, history):

        self.client.set(
            session_id,
            json.dumps(history),
            ex=3600
        )

    def append_message(self, session_id, role, message):

        history = self.get_history(session_id)

        history.append({
            "role": role,
            "message": message
        })

        self.save_history(session_id, history)

        return history