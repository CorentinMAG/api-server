"""
Centralized configuration management for the API Server.

This module reads environment variables, sets up default values,
and initializes a structured logger for the entire application.
It follows the standard DTR pod architecture for configuration.
"""
from __future__ import annotations

import os

from dtr_common.logs.logger import create_logger

# --- Core Application Identity ---
API_SERVER_VERSION = os.environ.get("DTR_API_SERVER_VERSION", "0.0.0-dev")
SYSTEM_NAME = "dtr"
SYSTEM_VERSION = os.environ.get("DTR_VERSION", "0.0.0-dev")

# --- Logging Configuration ---
LOG_LEVEL = os.environ.get("DTR_LOG_LEVEL", "INFO")

# --- Flask Environment ---
FLASK_ENV = os.environ.get("FLASK_ENV", "production")
TESTING = os.environ.get("FLASK_TESTING", "false").lower() == "true"
IS_DEBUG = LOG_LEVEL == "DEBUG"

# --- Database Configuration ---
DB_USER = os.environ.get("DTR_DB_USER", "dtr")
DB_PASSWORD = os.environ.get("DTR_DB_PASSWORD")
DB_NAME = os.environ.get("DTR_DB_NAME", "postgres")
DB_HOST = os.environ.get("DTR_DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DTR_DB_PORT", 5438))
CREATE_DB = os.environ.get("DTR_DB_CREATE", "false").lower() == "true"
DATABASE_URL = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}" if DB_PASSWORD else None
)

SQLALCHEMY_ENGINE_OPTIONS = {}

if TESTING:
    DATABASE_URL = "sqlite:///:memory:"
else:
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 15,
        "max_overflow": 25,
        "pool_timeout": 30,
    }

# --- Security ---
ENCRYPTION_KEY = os.environ.get("DTR_ENCRYPTION_KEY")

# --- Logger Initialization ---
logger = create_logger("api-server", LOG_LEVEL, API_SERVER_VERSION, SYSTEM_NAME, SYSTEM_VERSION)

# --- Initial Configuration Logging ---
logger.info(
    "API Server configuration loaded",
    extra={
        "config": {
            "version": API_SERVER_VERSION,
            "system_version": SYSTEM_VERSION,
            "log_level": LOG_LEVEL,
            "flask_env": FLASK_ENV,
        }
    },
)
logger.debug(
    "Database configuration", extra={"config": {"db_host": DB_HOST, "db_port": DB_PORT, "db_name": DB_NAME}}
)
