from __future__ import annotations
import os


class Config:
    """Base configuration"""

    # --- Core Application Identity ---
    API_SERVER_VERSION = os.environ.get("DTR_API_SERVER_VERSION")
    SYSTEM_NAME = "dtr"
    SYSTEM_VERSION = os.environ.get("DTR_VERSION")

    # --- Logging Configuration ---
    LOG_LEVEL = os.environ.get("DTR_LOG_LEVEL", "INFO")

    DEBUG = False
    TESTING = False

    # --- Database Configuration ---
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
    }

    # --- Security ---
    ENCRYPTION_KEY = os.environ.get("DTR_ENCRYPTION_KEY", "A9ZA3v0x5lcvyXqaGTWr")


class DeveloppementConfig(Config):
    """Development Configuration"""

    DEBUG = True
    TESTING = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 15,
        "max_overflow": 25,
        "pool_timeout": 30,
        "echo": True,
    }
    DATABASE_URL = "sqlite:///dtr.db"


class TestingConfiguration(Config):
    """Testing Configuration"""

    DEBUG = False
    TESTING = True


class ProductionConfiguration(Config):
    """Production configuration"""

    DEBUG = False
    TESTING = False


CONFIG = {
    "development": DeveloppementConfig,
    "testing": TestingConfiguration,
    "production": ProductionConfiguration,
    "default": DeveloppementConfig,
}


ENCRYPTION_KEY = Config.ENCRYPTION_KEY


def create_config(env: str | None = None) -> Config:
    """Create configuration based on environment name."""
    if env is None:
        env = os.environ.get("DTR_ENV", "default")
    config_class = CONFIG.get(env.lower(), CONFIG["default"])
    return config_class
