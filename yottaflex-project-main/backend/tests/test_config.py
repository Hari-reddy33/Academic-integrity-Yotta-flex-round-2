import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_database_defaults_to_postgresql():
    settings = Settings(_env_file=None)
    assert settings.database_url.startswith("postgresql+psycopg://")


def test_database_rejects_sqlite_url():
    with pytest.raises(ValidationError, match="DATABASE_URL must use PostgreSQL"):
        Settings(_env_file=None, database_url="sqlite:///./integrity.db")
