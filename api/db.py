from __future__ import annotations
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

    # Add engine options only if they exist (not for SQLite)
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
                from api.models import GlobalParameters
                db.create_all()

                # Create default global parameters if they don't exist

                existing_params = db.session.query(GlobalParameters).first()
                if not existing_params:
                    default_params = GlobalParameters()
                    db.session.add(default_params)
                    logger.debug("Default global parameters created.")

                # Ensure tables are committed immediately so other services can see them
                db.session.commit()
                logger.debug("Database tables have been created.")
        _initialize_database()
