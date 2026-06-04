from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://mullm:mullm_password@localhost:5432/mullm"
    
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
    
    # Environment
    environment: str = "development"
    log_level: str = "INFO"
    
    # Ports
    port: int = 8000
    
    class Config:
        env_file = ".env"


settings = Settings()
