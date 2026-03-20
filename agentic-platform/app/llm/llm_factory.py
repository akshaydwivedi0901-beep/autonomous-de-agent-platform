from langchain_groq import ChatGroq
from app.core.config import settings


def create_groq(model):

    return ChatGroq(
        groq_api_key=settings.GROQ_API_KEY,
        model_name=model,
        temperature=0
    )