"""Configuration settings for SearchX Backend."""
import os
from pathlib import Path


class Settings:
    """Configuration settings and environment security guards for SearchX Backend."""

    def __init__(self) -> None:
        self.PROJECT_NAME: str = "SearchX API"
        self.VERSION: str = "1.0.0"
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()

        admin_key = os.getenv("SEARCHX_ADMIN_KEY")
        if self.ENVIRONMENT in ("production", "prod"):
            if not admin_key or admin_key.strip() in ("", "searchx-admin-secret"):
                raise RuntimeError(
                    "FATAL SECURITY VIOLATION: In production mode (ENVIRONMENT='production'), "
                    "SEARCHX_ADMIN_KEY must be set to a secure, unique value and cannot be missing "
                    "or equal to the default 'searchx-admin-secret'."
                )
            self.ADMIN_API_KEY: str = admin_key.strip()
        else:
            self.ADMIN_API_KEY: str = (admin_key.strip() if admin_key else "searchx-admin-secret")

        self.INDEX_PATH: Path = Path(os.getenv("SEARCHX_INDEX_PATH", "searchx_index.bin"))
        _default_engine = (
            "core-engine/build/searchx_engine.exe"
            if os.name == "nt"
            else "core-engine/build/searchx_engine"
        )
        self.ENGINE_BIN: Path = Path(os.getenv("SEARCHX_ENGINE_BIN", _default_engine))
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///searchx.db")
        self.REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.CACHE_ENABLED: bool = os.getenv("SEARCHX_CACHE_ENABLED", "true").lower() in ("true", "1", "yes")
        self.CACHE_TTL: int = int(os.getenv("SEARCHX_CACHE_TTL", "300"))


settings = Settings()
