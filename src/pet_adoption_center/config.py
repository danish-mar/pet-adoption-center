"""Configuration settings loaded from environment or defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if available in project root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    database: str = os.getenv("POSTGRES_DB", "pet_adoption")
    user: str = os.getenv("POSTGRES_USER", "postgres")
    password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    database_url: str | None = os.getenv("DATABASE_URL")
    connect_timeout: int = int(os.getenv("POSTGRES_TIMEOUT", "3"))

    def get_connection_kwargs(self, target_db: str | None = None) -> dict:
        """Returns keyword arguments for psycopg.connect."""
        if self.database_url:
            return {"conninfo": self.database_url, "connect_timeout": self.connect_timeout}
        return {
            "host": self.host,
            "port": self.port,
            "dbname": target_db or self.database,
            "user": self.user,
            "password": self.password,
            "connect_timeout": self.connect_timeout,
        }

    def get_maintenance_kwargs(self) -> dict:
        """Connect to default 'postgres' database to verify/create target database."""
        if self.database_url:
            # If a full URL is provided, try connecting directly
            return {"conninfo": self.database_url, "connect_timeout": self.connect_timeout}
        return self.get_connection_kwargs(target_db="postgres")


db_config = DatabaseConfig()
