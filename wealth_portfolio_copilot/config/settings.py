"""Configuration settings for the Wealth & Portfolio Co-Pilot."""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration."""
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""
    
    # LLM Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    SLM_MODEL: str = "llama-3-8b-quantized"
    
    # Vector Database
    VECTOR_DB_PATH: str = "./data/vector_store"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Graph Database (Neo4j)
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    
    # MCP Servers
    MARKET_DATA_API_KEY: str = ""  # Alpha Vantage, Yahoo Finance, etc.
    SEC_EDGAR_EMAIL: str = "user@example.com"
    
    # Guardrails
    ENABLE_GUARDRAILS: bool = True
    COMPLIANCE_THRESHOLD: float = 0.85
    
    # Memory
    MAX_EPISODIC_MEMORY: int = 10  # Max turns to remember in conversation
    SEMANTIC_MEMORY_TOP_K: int = 5  # Top K results from semantic memory
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/copilot.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
