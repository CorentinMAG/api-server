from __future__ import annotations

import os

class Config:
    """Base configuration"""
    API_VERSION = os.environ.get("DTR_API_VERSION", "0.0.0-dev")
    SYSTEM_NAME = "DTR"
    SYSTEM_VERSION = os.environ.get("DTR_VERSION", "0.0.0-dev")

    LOG_LEVEL = os.environ.get("DTR_LOG_LEVEL", "INFO")

    DEBUG = False
    TESTING = False

    # Databse configuration
    DB_USER = os.environ.get("DTR_DB_USER", "dtruser")
    DB_PASSWORD = os.environ.get("DTR_DB_PASSWORD")
    DB_NAME = os.environ.get("DTR_DB_NAME", "dtr")
    DB_HOST = os.environ.get("DTR_DB_HOST", "127.0.0.1")
    DB_PORT = int(os.environ.get("DTR_DB_PORT", 5432))
    CREATE_DB = os.environ.get("DTR_DB_CREATE", "false").lower() == "true"
    DATABASE_URL = (
        f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}" if DB_PASSWORD else None
    )

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 15,
        "max_overflow": 25,
        "pool_timeout": 30,
        "echo": False
    }

    ENCRYPTION_KEY = os.environ.get("DTR_ENCRYPTION_KEY", "A9ZA3v0x5lcvyXqaGTWr")

class DevelopmentConfig(Config):
    """Developmenet configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 15,
        "max_overflow": 25,
        "pool_timeout": 30,
        "echo": True
    }

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestConfiguration(Config):
    """Test configuration"""
    TESTING = True
    DEBUG = False

config_by_name = {
    "DEV": DevelopmentConfig,
    "TEST": TestConfiguration,
    "PROD": ProductionConfig,
    "DEFAULT": DevelopmentConfig
}

ENCRYPTION_KEY = Config.ENCRYPTION_KEY

def get_config(name: str | None = None) -> Config:
    """get configuration class by name"""
    if name is None:
        name = os.environ.get("DTR_ENVIRONMENT", "DEV").upper()
    
    # raise an error if the environement doesn't exist
    # prevent the application from booting
    return config_by_name[name]
