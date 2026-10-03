"""
Application Configuration and Environment Settings.
Strictly adhering to SDD specifications.
Loads .env reliably regardless of current working directory.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BASE_DIR.parent if BASE_DIR.name == "backend" else BASE_DIR

# Ensure sys.path contains ROOT_DIR and BASE_DIR
for _p in [str(ROOT_DIR), str(BASE_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Explicitly load .env from ROOT_DIR and BASE_DIR with override
for env_path in [ROOT_DIR / ".env", BASE_DIR / ".env", Path(".env")]:
    if env_path.exists():
        load_dotenv(dotenv_path=str(env_path), override=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "EDITH - Autonomous Job Intelligence Platform"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Database (PostgreSQL / SQLite)
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/data_intelligence.db")
    
    # AI & Search Keys (auto-stripped of whitespace)
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "").strip()
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY", "").strip()
    FIRECRAWL_API_URL: str = os.getenv("FIRECRAWL_API_URL", "https://api.firecrawl.dev").strip()
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # Exports directory
    EXPORTS_DIR: str = str(BASE_DIR / "exports")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure values from os.environ take effect and are trimmed
        if not self.FIRECRAWL_API_KEY:
            self.FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "").strip()
        else:
            self.FIRECRAWL_API_KEY = self.FIRECRAWL_API_KEY.strip()
            
        if not self.GEMINI_API_KEY:
            self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
        else:
            self.GEMINI_API_KEY = self.GEMINI_API_KEY.strip()

    class Config:
        env_file = [str(ROOT_DIR / ".env"), str(BASE_DIR / ".env"), ".env"]
        extra = "allow"

settings = Settings()
