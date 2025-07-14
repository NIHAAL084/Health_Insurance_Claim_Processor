"""Configuration management for the Health Insurance Claim Processor"""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict



class Settings(BaseSettings):
    """Application settings with sensible defaults"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8", 
        env_ignore_empty=True,
        extra="ignore"
    )

    # Google AI API Configuration
    google_api_key: str = "your_gemini_api_key_here"
    google_genai_use_vertex_ai: bool = False

    # Ollama Configuration
    ollama_model: str = "llama3.2:3b"
    ollama_url: str = "http://localhost:11434"

    # FastAPI Configuration
    app_name: str = "Health Insurance Claim Processor"
    app_version: str = "0.1.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8003

    # Database Configuration (optional)
    database_url: str = "sqlite:///./sessions.db"
    redis_url: str = "redis://localhost:6379"

    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"

    # File Upload Configuration
    max_file_size: int = 10485760
    allowed_extensions: str = "pdf"

    # Agent Configuration
    max_parallel_agents: int = 4
    agent_timeout: int = 1200  # Increased to 15 minutes for complex parallel processing


def is_running_in_docker() -> bool:
    """Check if the application is running inside a Docker container"""
    return os.path.exists('/.dockerenv')

def get_ollama_url() -> str:
    """Get the appropriate Ollama URL based on the environment"""
    base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    if is_running_in_docker():
        base_url = base_url.replace("localhost", "host.docker.internal")
    return base_url


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
