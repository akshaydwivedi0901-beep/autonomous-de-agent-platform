from langchain_groq import ChatGroq
from app.core.config import settings
import time
import logging

logger = logging.getLogger(__name__)


class SafeLLM:
    def __init__(self, llm):
        self.llm = llm

    def invoke(self, prompt):

        retries = 3

        for attempt in range(retries):
            try:
                return self.llm.invoke(prompt)

            except Exception as e:

                error_msg = str(e)

                # 🔥 Handle rate limit (429)
                if "429" in error_msg or "rate limit" in error_msg.lower():
                    wait_time = 2 ** attempt
                    logger.warning(f"⚠️ Rate limited. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                # 🔥 Unknown error
                logger.error(f"❌ LLM ERROR: {error_msg}")
                break

        # 🚨 FINAL FALLBACK (NO EXCEPTION)
        logger.error("🚨 LLM FAILED AFTER RETRIES — RETURNING FALLBACK")

        class FallbackResponse:
            content = "Unable to process request due to high load. Please try again."

        return FallbackResponse()


class LLMRouter:

    _cache = {}

    @classmethod
    def get_llm(cls, task: str, query: str = ""):
        """
        Return an LLM instance based on task type
        """

        model = cls._select_model(task, query)

        if model in cls._cache:
            return cls._cache[model]

        base_llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=model,
            temperature=0
        )

        # ✅ Wrap with SafeLLM
        llm = SafeLLM(base_llm)

        cls._cache[model] = llm

        return llm

    @staticmethod
    def _select_model(task: str, query: str):

        if task == "router":
            return settings.SMALL_MODEL

        if task == "planner":
            return settings.SMALL_MODEL

        if task == "sql":
            return settings.LARGE_MODEL

        if task == "validator":
            return settings.SMALL_MODEL

        if task == "explain":
            return settings.SMALL_MODEL

        if task == "reflection":
            return settings.SMALL_MODEL

        return settings.DEFAULT_MODEL