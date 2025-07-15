"""
Shared fixtures for API server tests.

This file provides common fixtures for mocking, environment setup,
and creating test clients and database sessions, making tests
more maintainable and readable.
"""

from __future__ import annotations

import os
import tempfile
from unittest.mock import Mock

import pytest

# Ensure critical env vars are set before any application modules import
os.environ.setdefault("DTR_ENCRYPTION_KEY", "test-key-that-is-32-bytes-long")
os.environ.setdefault("FLASK_TESTING", "True")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture
def mock_logger():
    """Mock the logger for all tests to prevent actual logging."""
    return Mock()


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """
    Set up a clean, predictable testing environment by setting
    all required environment variables before each test.
    """
    # Create a temporary file for SQLite test database
    test_db_fd, test_db_path = tempfile.mkstemp()
    os.close(test_db_fd)

    test_env_vars = {
        "DTR_API_SERVER_VERSION": "1.0.0-test",
        "DTR_VERSION": "2.0.0-test",
        "DTR_LOG_LEVEL": "DEBUG",
        "DTR_DB_USER": "test_user",
        "DTR_DB_PASSWORD": "test_password",
        "DTR_DB_NAME": "test_db",
        "DTR_DB_HOST": "localhost",
        "DTR_DB_PORT": "5433",
        "DTR_DB_CREATE": "true",
        "FLASK_ENV": "testing",
        "FLASK_TESTING": "True",
        "DATABASE_URL": f"sqlite:///{test_db_path}",
    }
    for key, value in test_env_vars.items():
        monkeypatch.setenv(key, value)
    yield

    # Clean up the test database file
    try:
        os.unlink(test_db_path)
    except OSError:
        pass


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    from api import create_app

    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def db_session():
    """Create a database session for testing."""
    from api import create_app
    from api.db import db

    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        # Create all tables
        db.create_all()

        # Create a session
        session = db.session

        yield session

        # Clean up after each test
        session.rollback()
        session.close()

        # Drop all tables
        db.drop_all()
