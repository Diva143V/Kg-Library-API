"""
Centralized configuration for KG Library API.
All settings are read from environment variables, enabling fully domain-agnostic deployment.
Set KG_LIBRARY_DATABASE_URL to switch from in-memory to a persistent PostgreSQL/SQLite backend.
"""

import os
import logging
from typing import Optional


class Settings:
    """
    Single source of truth for all runtime configuration.
    All values are read from environment variables with safe defaults.
    """

    def __init__(self) -> None:
        # --- Database ---
        self.database_url: Optional[str] = os.getenv("KG_LIBRARY_DATABASE_URL")

        # --- Logging ---
        self.log_level: str = os.getenv("KG_LIBRARY_LOG_LEVEL", "INFO").upper()

        # --- AI Gateway ---
        self.ai_enabled: bool = os.getenv("KG_LIBRARY_AI_ENABLED", "true").lower() == "true"
        self.max_ai_calls: int = int(os.getenv("KG_LIBRARY_MAX_AI_CALLS", "2"))
        self.ai_budget: float = float(os.getenv("KG_LIBRARY_AI_BUDGET", "0.01"))
        self.local_first: bool = os.getenv("KG_LIBRARY_LOCAL_FIRST", "true").lower() == "true"
        self.cloud_fallback: bool = os.getenv("KG_LIBRARY_CLOUD_FALLBACK", "false").lower() == "true"

        # --- API ---
        self.cors_origins: list = os.getenv("KG_LIBRARY_CORS_ORIGINS", "*").split(",")

    def configure_logging(self) -> None:
        """Apply the configured log level to the root logger."""
        logging.basicConfig(
            level=getattr(logging, self.log_level, logging.INFO),
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )


# Module-level singleton — imported everywhere
settings = Settings()
