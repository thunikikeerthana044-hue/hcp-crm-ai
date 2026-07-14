"""
Central configuration, loaded from environment variables (.env).
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # --- Groq / LLM ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    GROQ_MODEL_FALLBACK: str = os.getenv("GROQ_MODEL_FALLBACK", "llama-3.3-70b-versatile")

    # --- Database ---
    # Defaults to a local SQLite file so the project runs with zero setup.
    # For the required stack, point this at Postgres/MySQL instead, e.g.:
    #   postgresql+psycopg2://user:password@localhost:5432/hcp_crm
    #   mysql+pymysql://user:password@localhost:3306/hcp_crm
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./hcp_crm.db")

    # --- App ---
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")


settings = Settings()
