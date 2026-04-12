import json
import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)

SCHEMA_TTL = 3600
RESULT_TTL = 300

class CacheService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            try:
                import redis
                from app.core.config import settings
                cls._instance.client = redis.Redis.from_url(
                    settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2)
                cls._instance.client.ping()
                cls._instance._available = True
            except Exception as e:
                logger.warning(f"Cache unavailable: {e}")
                cls._instance._available = False
        return cls._instance

    @staticmethod
    def _query_key(question: str, environment: str) -> str:
        normalized = question.lower().strip()
        fingerprint = hashlib.sha256(f"{normalized}:{environment}".encode()).hexdigest()[:16]
        return f"query_result:{fingerprint}"

    def get_schema(self, db_type: str) -> Optional[dict]:
        if not self._available:
            return None
        try:
            data = self.client.get(f"schema:{db_type}")
            return json.loads(data) if data else None
        except Exception:
            return None

    def set_schema(self, db_type: str, schema: dict) -> None:
        if not self._available:
            return
        try:
            self.client.set(f"schema:{db_type}", json.dumps(schema), ex=SCHEMA_TTL)
        except Exception:
            pass

    def invalidate_schema(self, db_type: str) -> None:
        if not self._available:
            return
        try:
            self.client.delete(f"schema:{db_type}")
        except Exception:
            pass

    def get_query_result(self, question: str, environment: str) -> Optional[dict]:
        if not self._available:
            return None
        try:
            data = self.client.get(self._query_key(question, environment))
            return json.loads(data) if data else None
        except Exception:
            return None

    def set_query_result(self, question: str, environment: str, result: dict, ttl: int = RESULT_TTL) -> None:
        if not self._available:
            return
        try:
            self.client.set(self._query_key(question, environment), json.dumps(result), ex=ttl)
        except Exception:
            pass

    def get_stats(self) -> dict:
        if not self._available:
            return {"available": False}
        try:
            info = self.client.info("stats")
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 1)
            return {"available": True, "hits": hits, "misses": misses,
                    "hit_rate": round(hits / max(hits + misses, 1) * 100, 2)}
        except Exception as e:
            return {"available": False, "error": str(e)}

cache = CacheService()
