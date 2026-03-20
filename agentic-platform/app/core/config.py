import os
from dotenv import load_dotenv

load_dotenv()


class Settings:

    # =============================
    # ENVIRONMENT
    # =============================

    ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")

    # =============================
    # LLM CONFIG
    # =============================

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    SMALL_MODEL = os.getenv("SMALL_MODEL", "llama3-8b-8192")
    LARGE_MODEL = os.getenv("LARGE_MODEL", "mixtral-8x7b-32768")
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3-8b-8192")

    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 2048))

    # =============================
    # VECTOR DATABASE
    # =============================

    VECTOR_DB = os.getenv("VECTOR_DB", "chroma")

    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")

    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    # =============================
    # REDIS (MEMORY + QUEUES)
    # =============================

    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))

    # =============================
    # INGESTION SETTINGS
    # =============================

    MAX_CHUNK_SIZE = int(os.getenv("MAX_CHUNK_SIZE", 1000))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))

    MAX_DOCUMENT_SIZE_MB = int(os.getenv("MAX_DOCUMENT_SIZE_MB", 25))

    # =============================
    # SNOWFLAKE CONFIG
    # =============================

    SNOWFLAKE_CONFIG = {
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database": os.getenv("SNOWFLAKE_DATABASE"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA"),
        "role": os.getenv("SNOWFLAKE_ROLE"),
    }

    # =============================
    # AGENT SETTINGS
    # =============================

    MAX_AGENT_STEPS = int(os.getenv("MAX_AGENT_STEPS", 5))

    ENABLE_RAG = os.getenv("ENABLE_RAG", "true").lower() == "true"

    ENABLE_SQL_TOOL = os.getenv("ENABLE_SQL_TOOL", "true").lower() == "true"

    ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "true").lower() == "true"

    # =============================
    # GOVERNANCE / SAFETY
    # =============================

    ENABLE_CONTENT_FILTER = os.getenv(
        "ENABLE_CONTENT_FILTER",
        "true"
    ).lower() == "true"

    ENABLE_AUDIT_LOGS = os.getenv(
        "ENABLE_AUDIT_LOGS",
        "true"
    ).lower() == "true"


settings = Settings()