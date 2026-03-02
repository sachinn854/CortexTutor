"""
Configuration management for the YouTube Learning Assistant.
Loads environment variables and provides application settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    app_name: str = "YouTube Learning Assistant"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Ollama Configuration (Local LLM - FREE!)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"  # Fast, good quality (2GB)
    
    # Embedding Model
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Vector Database Configuration
    vector_db_type: str = "faiss"  # Using FAISS (no Rust compilation needed)
    vector_db_path: str = "./vector_db"
    
    # RAG Configuration
    chunk_size: int = 300  # Very small chunks to fit Groq free tier
    chunk_overlap: int = 50  # Minimal overlap
    retrieval_top_k: int = 2  # Only 2 chunks to reduce tokens
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS Configuration
    cors_origins: str = "*"  # Allow all origins for development
    
    @property
    def cors_origins_list(self) -> list:
        """Convert comma-separated CORS origins to list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings


# Validate critical settings
if __name__ != "__main__":
    # No validation needed for Ollama - it's local!
    pass
