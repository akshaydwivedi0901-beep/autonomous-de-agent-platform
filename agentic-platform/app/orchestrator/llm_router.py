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

from dataclasses import dataclass

MODELS = {
    "nano":   "llama-3.1-8b-instant",
    "small":  "llama-3.1-8b-instant",
    "medium": "llama-3.3-70b-versatile",
    "large":  "llama-3.3-70b-versatile",
}

@dataclass
class ComplexityScore:
    score: int
    tier: str
    model: str
    reasons: list

def score_query_complexity(question: str) -> ComplexityScore:
    q = question.lower()
    score = 0
    reasons = []
    simple = ["how many", "count", "total", "what is", "show me", "list"]
    if any(k in q for k in simple):
        score += 5
    medium = ["average", "avg", "top", "rank", "compare", "between", "per month", "per year", "group"]
    hits = sum(1 for k in medium if k in q)
    score += hits * 10
    joins = ["join", "with", "combined", "across"]
    score += sum(1 for k in joins if k in q) * 15
    complex_kw = ["running total", "cumulative", "window", "lag", "lead", "percentile",
                  "rank over", "moving average", "year over year", "month over month",
                  "growth rate", "correlation"]
    score += sum(1 for k in complex_kw if k in q) * 25
    entities = ["customer", "order", "supplier", "part", "lineitem", "nation"]
    ec = sum(1 for e in entities if e in q)
    if ec > 2:
        score += (ec - 2) * 10
    if len(q.split()) > 20:
        score += 10
    score = min(score, 100)
    if score <= 20:
        tier, model = "nano", MODELS["nano"]
    elif score <= 40:
        tier, model = "small", MODELS["small"]
    elif score <= 70:
        tier, model = "medium", MODELS["medium"]
    else:
        tier, model = "large", MODELS["large"]
    return ComplexityScore(score=score, tier=tier, model=model, reasons=reasons)
