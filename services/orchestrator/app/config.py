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

    # Environment
    environment: str = "development"
    log_level: str = "INFO"
    
    # Ports
    port: int = 8000
    
    class Config:
        env_file = ".env"


settings = Settings()
