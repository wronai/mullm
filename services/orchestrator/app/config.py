from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database (projections + postgres event store)
    database_url: str = "postgresql://mullm:mullm_password@localhost:5432/mullm"

    # Event store: postgres | eventstoredb | dual
    event_store_backend: str = "postgres"
    eventstore_url: str = "esdb://localhost:2113?tls=false"
    
    # NATS
    nats_url: str = "nats://localhost:4222"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Service
    service_name: str = "orchestrator"
    service_version: str = "1.0.0"
    
    # Security
    jwt_secret: str = "your_jwt_secret_here"
    api_key: str = "your_api_key_here"
    
    # Architecture catalog (repo root / catalog)
    catalog_path: str = ""  # env: CATALOG_PATH

    # OpenRouter (RAG + optional LLM answers)
    openrouter_api_key: str = ""
    llm_model: str = "openrouter/deepseek/deepseek-v4-pro"
    embedding_model: str = "openai/text-embedding-3-small"
    rag_auto_ingest: bool = True

    # Environment
    environment: str = "development"
    log_level: str = "INFO"
    
    # Ports
    port: int = 8000
    
    class Config:
        env_file = ".env"


settings = Settings()
