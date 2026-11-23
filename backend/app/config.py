"""Configuration settings for SearchX Backend."""
import os
from pathlib import Path


class Settings:
    PROJECT_NAME: str = "SearchX API"
    VERSION: str = "1.0.0"
    ADMIN_API_KEY: str = os.getenv("SEARCHX_ADMIN_KEY", "searchx-admin-secret")
    INDEX_PATH: Path = Path(os.getenv("SEARCHX_INDEX_PATH", "searchx_index.bin"))
    ENGINE_BIN: Path = Path(os.getenv("SEARCHX_ENGINE_BIN", "core-engine/build/searchx_engine.exe"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///searchx.db")


settings = Settings()
