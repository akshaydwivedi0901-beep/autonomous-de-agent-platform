import os
from dotenv import load_dotenv

load_dotenv()


class Settings:

    # =============================
    # ENVIRONMENT
    # =============================
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")

    # =============================
    # SECURITY
    # =============================
    API_KEY: str = os.getenv("API_KEY", "")
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "*").split(",")

    # =============================
    # LLM
    # =============================
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    SMALL_MODEL: str = os.getenv("SMALL_MODEL", "llama-3.1-8b-instant")
    LARGE_MODEL: str = os.getenv("LARGE_MODEL", "llama3-70b-8192")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "llama-3.1-8b-instant")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", 2048))

    # =============================
    # DATABASE
    # =============================
    DB_TYPE: str = os.getenv("DB_TYPE", "snowflake")

    SNOWFLAKE_CONFIG: dict = {
        "user":      os.getenv("SNOWFLAKE_USER"),
        "password":  os.getenv("SNOWFLAKE_PASSWORD"),
        "account":   os.getenv("SNOWFLAKE_ACCOUNT"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database":  os.getenv("SNOWFLAKE_DATABASE"),
        "schema":    os.getenv("SNOWFLAKE_SCHEMA"),
        "role":      os.getenv("SNOWFLAKE_ROLE"),
    }

    POSTGRES_URL: str = os.getenv("POSTGRES_URL", "")
    BIGQUERY_PROJECT: str = os.getenv("BIGQUERY_PROJECT", "")
    BIGQUERY_DATASET: str = os.getenv("BIGQUERY_DATASET", "")
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "")
    MYSQL_USER: str = os.getenv("MYSQL_USER", "")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "")

    # =============================
    # VECTOR DB
    # =============================
    VECTOR_DB: str = os.getenv("VECTOR_DB", "chroma")
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", os.getenv("CHROMA_DB_PATH", "./chroma_db"))
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENV: str = os.getenv("PINECONE_ENV", "")
    PINECONE_INDEX: str = os.getenv("PINECONE_INDEX", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    # =============================
    # REDIS
    # =============================
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # =============================
    # INGESTION
    # =============================
    MAX_CHUNK_SIZE: int = int(os.getenv("MAX_CHUNK_SIZE", 1000))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 200))
    MAX_DOCUMENT_SIZE_MB: int = int(os.getenv("MAX_DOCUMENT_SIZE_MB", 25))

    # =============================
    # AGENT
    # =============================
    MAX_AGENT_STEPS: int = int(os.getenv("MAX_AGENT_STEPS", 5))
    ENABLE_RAG: bool = os.getenv("ENABLE_RAG", "true").lower() == "true"
    ENABLE_SQL_TOOL: bool = os.getenv("ENABLE_SQL_TOOL", "true").lower() == "true"
    ENABLE_MEMORY: bool = os.getenv("ENABLE_MEMORY", "true").lower() == "true"

    # =============================
    # GOVERNANCE
    # =============================
    ENABLE_CONTENT_FILTER: bool = os.getenv("ENABLE_CONTENT_FILTER", "true").lower() == "true"
    ENABLE_AUDIT_LOGS: bool = os.getenv("ENABLE_AUDIT_LOGS", "true").lower() == "true"


# Plain class instantiation — no Pydantic
settings = Settings()