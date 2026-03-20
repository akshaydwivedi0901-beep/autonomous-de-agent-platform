from langchain_groq import ChatGroq
from app.core.config import settings


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

        llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=model,
            temperature=0
        )

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