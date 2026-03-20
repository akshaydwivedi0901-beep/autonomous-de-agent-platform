from langchain_community.vectorstores import Chroma
from app.rag.embeddings import get_embedding_model
from app.core.config import settings


def get_vector_store():

    embeddings = get_embedding_model()

    if settings.VECTOR_DB == "chroma":
        return Chroma(
            persist_directory=settings.VECTOR_DB_PATH,
            embedding_function=embeddings,
        )

    if settings.VECTOR_DB == "pinecone":
        import pinecone
        from langchain_pinecone import PineconeVectorStore

        pinecone.init(
            api_key=settings.PINECONE_API_KEY,
            environment=settings.PINECONE_ENV,
        )

        return PineconeVectorStore(
            index_name=settings.PINECONE_INDEX,
            embedding=embeddings,
        )

    raise ValueError("Unsupported vector DB")