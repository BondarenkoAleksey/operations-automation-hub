import pytest
from pydantic import ValidationError

from operations_automation_hub.core.settings import Settings


def test_settings_loads_postgres_values_from_environment(monkeypatch):
    monkeypatch.setenv("POSTGRES_DB", "test_operations_automation_hub")
    monkeypatch.setenv("POSTGRES_HOST", "test-db")
    monkeypatch.setenv("POSTGRES_USER", "test-user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_password_123")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    settings = Settings(_env_file=None)
    assert settings.postgres_db == "test_operations_automation_hub"
    assert settings.postgres_host == "test-db"
    assert settings.postgres_user == "test-user"
    assert settings.postgres_password == "test_password_123"
    assert settings.postgres_port == 5432


def test_settings_builds_postgres_database_url(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "test-db")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "test_operations_automation_hub")
    monkeypatch.setenv("POSTGRES_USER", "test-user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_password_123")
    settings = Settings(_env_file=None)
    url = settings.database_url
    assert url.drivername == "postgresql+psycopg"
    assert url.host == "test-db"
    assert url.port == 5432
    assert url.database == "test_operations_automation_hub"
    assert url.username == "test-user"


def test_settings_rejects_non_integer_postgres_port(monkeypatch):
    monkeypatch.setenv("POSTGRES_DB", "test_operations_automation_hub")
    monkeypatch.setenv("POSTGRES_HOST", "test-db")
    monkeypatch.setenv("POSTGRES_USER", "test-user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_password_123")
    monkeypatch.setenv("POSTGRES_PORT", "invalid-port")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
