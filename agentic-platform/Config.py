"""
Configuration module for the agent platform.
Manages environment variables and application settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    
    # =============================
    # Application Settings
    # =============================
    APP_NAME: str = Field(default="AI Agent Platform", env="APP_NAME")
    APP_ENV: str = Field(default="development", env="APP_ENV")
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # =============================
    # Server Settings
    # =============================
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=4, env="WORKERS")
    RELOAD: bool = Field(default=False, env="RELOAD")
    
    # =============================
    # API Settings
    # =============================
    API_KEY: str = Field(default="", env="API_KEY")
    API_VERSION: str = Field(default="v1", env="API_VERSION")
    API_TIMEOUT: int = Field(default=30, env="API_TIMEOUT")
    
    # =============================
    # LLM Settings
    # =============================
    GROQ_API_KEY: str = Field(default="", env="GROQ_API_KEY")
    LLM_MODEL: str = Field(default="mixtral-8x7b-32768", env="LLM_MODEL")
    LLM_TEMPERATURE: float = Field(default=0.7, env="LLM_TEMPERATURE")
    LLM_MAX_TOKENS: int = Field(default=2048, env="LLM_MAX_TOKENS")
    
    # =============================
    # Snowflake Settings
    # =============================
    SNOWFLAKE_USER: str = Field(default="", env="SNOWFLAKE_USER")
    SNOWFLAKE_PASSWORD: str = Field(default="", env="SNOWFLAKE_PASSWORD")
    SNOWFLAKE_ACCOUNT: str = Field(default="", env="SNOWFLAKE_ACCOUNT")
    SNOWFLAKE_WAREHOUSE: str = Field(default="", env="SNOWFLAKE_WAREHOUSE")
    SNOWFLAKE_DATABASE: str = Field(default="", env="SNOWFLAKE_DATABASE")
    SNOWFLAKE_SCHEMA: str = Field(default="", env="SNOWFLAKE_SCHEMA")
    SNOWFLAKE_ROLE: str = Field(default="", env="SNOWFLAKE_ROLE")
    
    # =============================
    # Redis Settings
    # =============================
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_SSL: bool = Field(default=False, env="REDIS_SSL")
    
    # =============================
    # Database Settings
    # =============================
    DATABASE_URL: str = Field(default="", env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    
    # =============================
    # Feature Flags
    # =============================
    ENABLE_RAG: bool = Field(default=False, env="ENABLE_RAG")
    ENABLE_CACHING: bool = Field(default=True, env="ENABLE_CACHING")
    ENABLE_MONITORING: bool = Field(default=True, env="ENABLE_MONITORING")
    ENABLE_RATE_LIMITING: bool = Field(default=True, env="ENABLE_RATE_LIMITING")
    
    # =============================
    # RAG Settings
    # =============================
    VECTOR_STORE_TYPE: str = Field(default="pinecone", env="VECTOR_STORE_TYPE")
    EMBEDDING_MODEL: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    PINECONE_API_KEY: Optional[str] = Field(default=None, env="PINECONE_API_KEY")
    PINECONE_ENVIRONMENT: Optional[str] = Field(default=None, env="PINECONE_ENVIRONMENT")
    PINECONE_INDEX: str = Field(default="ai-agent", env="PINECONE_INDEX")
    
    # =============================
    # Monitoring & Telemetry
    # =============================
    ENABLE_TELEMETRY: bool = Field(default=True, env="ENABLE_TELEMETRY")
    METRICS_PORT: int = Field(default=8001, env="METRICS_PORT")
    JAEGER_ENABLED: bool = Field(default=False, env="JAEGER_ENABLED")
    JAEGER_AGENT_HOST: str = Field(default="localhost", env="JAEGER_AGENT_HOST")
    JAEGER_AGENT_PORT: int = Field(default=6831, env="JAEGER_AGENT_PORT")
    
    # =============================
    # Authentication Settings
    # =============================
    JWT_SECRET: Optional[str] = Field(default=None, env="JWT_SECRET")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRATION: int = Field(default=3600, env="JWT_EXPIRATION")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings instance.
    
    Returns:
        Settings instance with all configuration
    """
    return settings


def get_snowflake_config() -> dict:
    """
    Get Snowflake configuration dictionary.
    
    Returns:
        Dictionary with Snowflake connection parameters
    """
    return {
        "user": settings.SNOWFLAKE_USER,
        "password": settings.SNOWFLAKE_PASSWORD,
        "account": settings.SNOWFLAKE_ACCOUNT,
        "warehouse": settings.SNOWFLAKE_WAREHOUSE,
        "database": settings.SNOWFLAKE_DATABASE,
        "schema": settings.SNOWFLAKE_SCHEMA,
        "role": settings.SNOWFLAKE_ROLE,
    }


def get_redis_config() -> dict:
    """
    Get Redis configuration dictionary.
    
    Returns:
        Dictionary with Redis connection parameters
    """
    return {
        "host": settings.REDIS_HOST,
        "port": settings.REDIS_PORT,
        "db": settings.REDIS_DB,
        "password": settings.REDIS_PASSWORD,
        "ssl": settings.REDIS_SSL,
    }


def is_production() -> bool:
    """
    Check if application is running in production.
    
    Returns:
        True if APP_ENV is 'production'
    """
    return settings.APP_ENV.lower() == "production"


def is_development() -> bool:
    """
    Check if application is running in development.
    
    Returns:
        True if APP_ENV is 'development'
    """
    return settings.APP_ENV.lower() == "development"
