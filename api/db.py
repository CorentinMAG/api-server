from __future__ import annotations

from dtr_common.exceptions.errors import RetryError
from dtr_common.retry import retry_database_operation
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy_utils import create_database, database_exists

from config import CREATE_DB, DATABASE_URL, SQLALCHEMY_ENGINE_OPTIONS, logger


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


def init_app(app: Flask):
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not configured. Please check your environment variables.")

    # Base configuration
    config = {
        "SQLALCHEMY_DATABASE_URI": DATABASE_URL,
    }

    # Add engine options only if they exist
    if SQLALCHEMY_ENGINE_OPTIONS:
        config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "echo_pool": True,
            **SQLALCHEMY_ENGINE_OPTIONS,
        }

    app.config.update(config)

    db.init_app(app)

    if CREATE_DB:
        def _initialize_database():
            """Initialize database with proper error handling and retry."""
            # create database if it does not exists
            engine = create_engine(DATABASE_URL)
            if not database_exists(engine.url):
                create_database(engine.url)
                logger.info("New database created.", extra={"db_url": engine.url})
            else:
                # Connect to the database if exits
                engine.connect()
                logger.debug("Connected to existing database.", extra={"db_url": engine.url})

            # create all tables
            with app.app_context():
                db.create_all()
                logger.debug("Database tables have been created.")

        try:
            retry_database_operation(
                _initialize_database,
                logger=logger,
                total=5,
                backoff_factor=2,
                initial_delay=2,
                max_delay=30
            )
        except RetryError as e:
            logger.error(f"Failed to initialize database after retries: {str(e)}")
            # Don't crash the application, let it try to connect later
            logger.warning("Application will start but database operations may fail until connection is restored")
