"""
Application Configuration and Environment Settings.
Strictly adhering to SDD specifications.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered Data Intelligence Platform"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Database (PostgreSQL / SQLite)
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/data_intelligence.db")
    
    # AI & Search Keys
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # Exports directory
    EXPORTS_DIR: str = str(BASE_DIR / "exports")

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
