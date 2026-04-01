import os
from dotenv import load_dotenv

load_dotenv()


class Settings:

    # =============================
    # ENVIRONMENT
    # =============================
    ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")

    # =============================
    # SECURITY
    # =============================
    API_KEY         = os.getenv("API_KEY")           # required in prod
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

    # =============================
    # LLM CONFIG
    # =============================
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")   # ← set via K8s Secret, never hardcode

    SMALL_MODEL   = os.getenv("SMALL_MODEL",   "llama-3.1-8b-instant")
    LARGE_MODEL   = os.getenv("LARGE_MODEL",   "llama3-70b-8192")
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama-3.1-8b-instant")

    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 2048))

    # =============================
    # DATABASE TYPE (routing)
    # =============================
    DB_TYPE = os.getenv("DB_TYPE", "snowflake")   # snowflake | postgres | bigquery | mysql

    # =============================
    # SNOWFLAKE
    # =============================
    SNOWFLAKE_CONFIG = {
        "user":      os.getenv("SNOWFLAKE_USER"),
        "password":  os.getenv("SNOWFLAKE_PASSWORD"),
        "account":   os.getenv("SNOWFLAKE_ACCOUNT"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database":  os.getenv("SNOWFLAKE_DATABASE"),
        "schema":    os.getenv("SNOWFLAKE_SCHEMA"),
        "role":      os.getenv("SNOWFLAKE_ROLE"),
    }

    # =============================
    # POSTGRES
    # =============================
    POSTGRES_URL = os.getenv("POSTGRES_URL", "")

    # =============================
    # BIGQUERY
    # =============================
    BIGQUERY_PROJECT = os.getenv("BIGQUERY_PROJECT", "")
    BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "")

    # =============================
    # MYSQL
    # =============================
    MYSQL_HOST     = os.getenv("MYSQL_HOST", "")
    MYSQL_USER     = os.getenv("MYSQL_USER", "")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "")

    # =============================
    # VECTOR DATABASE
    # =============================
    VECTOR_DB      = os.getenv("VECTOR_DB", "chroma")
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", CHROMA_DB_PATH)

    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENV     = os.getenv("PINECONE_ENV", "")
    PINECONE_INDEX   = os.getenv("PINECONE_INDEX", "")

    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2",
    )

    # =============================
    # REDIS
    # =============================
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # =============================
    # INGESTION
    # =============================
    MAX_CHUNK_SIZE       = int(os.getenv("MAX_CHUNK_SIZE", 1000))
    CHUNK_OVERLAP        = int(os.getenv("CHUNK_OVERLAP", 200))
    MAX_DOCUMENT_SIZE_MB = int(os.getenv("MAX_DOCUMENT_SIZE_MB", 25))

    # =============================
    # AGENT SETTINGS
    # =============================
    MAX_AGENT_STEPS = int(os.getenv("MAX_AGENT_STEPS", 5))

    ENABLE_RAG       = os.getenv("ENABLE_RAG",       "true").lower() == "true"
    ENABLE_SQL_TOOL  = os.getenv("ENABLE_SQL_TOOL",  "true").lower() == "true"
    ENABLE_MEMORY    = os.getenv("ENABLE_MEMORY",    "true").lower() == "true"

    # =============================
    # GOVERNANCE / SAFETY
    # =============================
    ENABLE_CONTENT_FILTER = os.getenv("ENABLE_CONTENT_FILTER", "true").lower() == "true"
    ENABLE_AUDIT_LOGS     = os.getenv("ENABLE_AUDIT_LOGS",     "true").lower() == "true"


settings = Settings()