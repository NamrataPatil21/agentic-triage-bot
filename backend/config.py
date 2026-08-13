import os
from pathlib import Path

try:
    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        """Application configuration loaded from environment variables or .env file."""
        GROQ_API_KEY: str = ""
        DB_FILE: str = "triage_bot.db"

        class Config:
            env_file = ".env"
            extra = "ignore"

    settings = Settings()
    # Ensure fallback to os.getenv if BaseSettings default is empty
    if not settings.GROQ_API_KEY:
        settings.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

except Exception:
    class Settings:
        """Fallback configuration class using os.getenv."""
        GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
        DB_FILE: str = os.getenv("DB_FILE", "triage_bot.db")

    settings = Settings()

def get_settings() -> Settings:
    """Returns the active Settings instance."""
    return settings
