import json
import logging
from typing import List, Dict, Optional

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

SESSION_TTL = 3600        # 1 hour session expiry
MAX_HISTORY_TURNS = 20    # cap stored turns per session


class RedisMemory:
    """
    Multi-turn conversation memory backed by Redis.

    Each session stores a capped list of turns:
      [{"role": "user"|"assistant"|"system", "message": "..."}]

    Safe: all operations fail gracefully — never breaks the main pipeline.
    """

    def __init__(self):
        try:
            self.client = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            self.client.ping()
            self._available = True
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable — memory disabled: {e}")
            self._available = False

    # =============================
    # READ
    # =============================
    def get_history(self, session_id: Optional[str]) -> List[Dict]:
        if not self._available or not session_id:
            return []

        try:
            data = self.client.get(self._key(session_id))
            return json.loads(data) if data else []
        except Exception as e:
            logger.warning(f"Redis get_history failed: {e}")
            return []

    # =============================
    # WRITE
    # =============================
    def save_history(self, session_id: str, history: List[Dict]) -> None:
        if not self._available or not session_id:
            return

        try:
            # Keep only recent turns to bound Redis memory
            trimmed = history[-MAX_HISTORY_TURNS:]
            self.client.set(
                self._key(session_id),
                json.dumps(trimmed),
                ex=SESSION_TTL,
            )
        except Exception as e:
            logger.warning(f"Redis save_history failed: {e}")

    # =============================
    # APPEND
    # =============================
    def append_message(
        self,
        session_id: Optional[str],
        role: str,
        message: str,
    ) -> List[Dict]:
        history = self.get_history(session_id)

        history.append({"role": role, "message": message})

        if session_id:
            self.save_history(session_id, history)

        return history

    # =============================
    # CONTEXT WINDOW (for prompts)
    # =============================
    def get_recent_context(
        self,
        session_id: Optional[str],
        turns: int = 6,
    ) -> List[Dict]:
        """Return the last N user/assistant turns, skipping system messages."""
        history = self.get_history(session_id)
        user_turns = [
            m for m in history
            if m.get("role") in ("user", "assistant")
        ]
        return user_turns[-turns:]

    # =============================
    # CLEAR
    # =============================
    def clear_session(self, session_id: str) -> None:
        if not self._available:
            return
        try:
            self.client.delete(self._key(session_id))
        except Exception as e:
            logger.warning(f"Redis clear_session failed: {e}")

    # =============================
    # HELPERS
    # =============================
    @staticmethod
    def _key(session_id: str) -> str:
        return f"session:{session_id}"
