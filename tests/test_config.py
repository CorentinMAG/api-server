"""
Unit tests for the centralized configuration module.

These tests ensure that all environment variables are loaded correctly,
default values are applied when expected, and the logger is
initialized properly. Achieving 100% coverage here is critical.
"""
from __future__ import annotations

import sys


def test_config_loads_all_environment_variables(setup_test_environment):
    """Verify that all environment variables are loaded correctly from the test environment."""
    # We re-import config here to ensure it's loaded after the test environment is set up
    if "config" in sys.modules:
        del sys.modules["config"]
    from config import (
        API_SERVER_VERSION,
        CREATE_DB,
        DATABASE_URL,
        DB_HOST,
        DB_NAME,
        DB_PASSWORD,
        DB_PORT,
        DB_USER,
        ENCRYPTION_KEY,
        FLASK_ENV,
        LOG_LEVEL,
        SYSTEM_VERSION,
    )

    assert API_SERVER_VERSION == "1.0.0-test"
    assert SYSTEM_VERSION == "2.0.0-test"
    assert LOG_LEVEL == "DEBUG"
    assert DB_USER == "test_user"
    assert DB_PASSWORD == "test_password"
    assert DB_NAME == "test_db"
    assert DB_HOST == "localhost"
    assert DB_PORT == 5433
    assert CREATE_DB is True
    assert ENCRYPTION_KEY == "test-key-that-is-32-bytes-long"
    assert FLASK_ENV == "testing"
    # In testing mode, DATABASE_URL should be SQLite
    assert DATABASE_URL == "sqlite:///:memory:"


def test_config_default_values(monkeypatch):
    """Test that default values are used when optional environment variables are not set."""
    # Unset optional variables to test defaults
    monkeypatch.delenv("DTR_LOG_LEVEL", raising=False)
    monkeypatch.delenv("FLASK_ENV", raising=False)
    monkeypatch.delenv("DTR_DB_USER", raising=False)
    monkeypatch.delenv("DTR_DB_NAME", raising=False)
    monkeypatch.delenv("DTR_DB_PORT", raising=False)
    monkeypatch.delenv("DTR_DB_CREATE", raising=False)

    # Set required variables
    monkeypatch.setenv("DTR_API_SERVER_VERSION", "1.0.0-test")
    monkeypatch.setenv("DTR_VERSION", "2.0.0-test")
    monkeypatch.setenv("DTR_DB_PASSWORD", "password")
    monkeypatch.setenv("DTR_DB_HOST", "db_host")
    monkeypatch.setenv("DTR_ENCRYPTION_KEY", "key")

    # Re-import config to apply changes
    if "config" in sys.modules:
        del sys.modules["config"]
    from config import CREATE_DB, DB_NAME, DB_PORT, DB_USER, FLASK_ENV, LOG_LEVEL

    assert LOG_LEVEL == "INFO"
    assert FLASK_ENV == "production"
    assert DB_USER == "dtr"
    assert DB_NAME == "postgres"
    assert DB_PORT == 5438
    assert CREATE_DB is False


def test_logger_initialization(setup_test_environment):
    """Verify that the logger is created and configured correctly."""
    # Re-import config to get the logger created with test settings
    if "config" in sys.modules:
        del sys.modules["config"]
    from config import logger

    assert logger is not None
    # The common logger might return a 'DevLogger' in non-production environments.
    # We'll just check that it's a valid logger instance.
    assert logger.name is not None
    assert logger.level == 10  # DEBUG
    assert len(logger.handlers) > 0
    assert hasattr(logger, "info")
    assert hasattr(logger, "debug")
