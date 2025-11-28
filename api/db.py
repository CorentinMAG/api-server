from __future__ import annotations
from flask import Flask
from sqlalchemy_utils import create_database, database_exists
from api.models import db
from .config import CREATE_DB, DATABASE_URL, SQLALCHEMY_ENGINE_OPTIONS, logger, DB_NAME

def init_app(app: Flask):

    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set, make sure to define the DTR_DB_PASSWORD variable")

    # Base configuration
    config = {
        "SQLALCHEMY_DATABASE_URI": DATABASE_URL,
        "SQLALCHEMY_ENGINE_OPTIONS": SQLALCHEMY_ENGINE_OPTIONS
    }

    app.config.update(config)
    db.init_app(app)
    
    if CREATE_DB:
        with app.app_context():
            if not database_exists(db.engine.url):
                create_database(db.engine.url)
                logger.info("New database %s created", DB_NAME)
            else:
                # create all tables
                from api.models import GlobalParameters
                db.create_all()

                # Create default global parameters if they don't exist
                existing_params = db.session.query(GlobalParameters).first()
                if not existing_params:
                    default_params = GlobalParameters()
                    db.session.add(default_params)
                    logger.debug("Default global parameters created")

                # Ensure tables are committed immediately so other services can see them
                db.session.commit()
                logger.debug("Database tables have been created")
