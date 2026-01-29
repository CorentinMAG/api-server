from __future__ import annotations

import os

class Config:
    """Base configuration"""

    API_VERSION = os.environ.get("DTR_API_SERVER_VERSION")
    SYSTEM_NAME = "DTR"
    SYSTEM_VERSION = os.environ.get("DTR_VERSION")

    LOG_LEVEL = os.environ.get("DTR_LOG_LEVEL", "INFO")

    DEBUG = False
    TESTING = False

    # Database configuration
    DB_USER = os.environ.get("DTR_DB_USER", "dtruser")
    DB_PASSWORD = os.environ.get("DTR_DB_PASSWORD")
    DB_NAME = os.environ.get("DTR_DB_NAME", "dtr")
    DB_HOST = os.environ.get("DTR_DB_HOST", "127.0.0.1")
    DB_PORT = int(os.environ.get("DTR_DB_PORT", 5432))
    CREATE_DB = os.environ.get("DTR_DB_CREATE", "false").lower() == "true"
    DATABASE_URL = (
        f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}" 
        if DB_PASSWORD 
        else None
    )

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 15,
        "max_overflow": 25,
        "pool_timeout": 30,
        "echo": False
    }

    ENCRYPTION_KEY = os.environ.get("DTR_ENCRYPTION_KEY")

class DevelopmentConfig(Config):
    """Development configuration"""
    
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 15,
        "max_overflow": 25,
        "pool_timeout": 30,
        "echo": True
    }
    DATABASE_URL = "sqlite+pysqlite:///dtr.db"

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestConfiguration(Config):
    """Test configuration"""
    TESTING = True
    DEBUG = False

    API_VERSION="api-test"
    SYSTEM_VERSION="api-test"
    DTR_DB_PASSWORD="azerty"

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 15,
        "max_overflow": 25,
        "pool_timeout": 30,
        "echo": True
    }
    DATABASE_URL = "sqlite+pysqlite:///dtr.db"

CONFIG = {
    "development": DevelopmentConfig,
    "testing": TestConfiguration,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}

ENCRYPTION_KEY = Config.ENCRYPTION_KEY

def create_config(env: str | None = None) -> Config:
    """get configuration based on environment variable"""
    if env is None:
        env = os.environ.get("DTR_ENV", "default")
    config_class = CONFIG.get(env.lower(), CONFIG["default"])
    return config_class
