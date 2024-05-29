import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from dtr_common.constantes import Mode
from sqlalchemy import  create_engine
from sqlalchemy_utils import database_exists, create_database  


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


def init_app(app: Flask):
    db_user = os.environ.get("DTR_DB_USER", "dtr")
    db_password = os.environ["DTR_DB_PASSWORD"]
    db_name = os.environ.get("DTR_DB_NAME", "postgres")
    db_host = os.environ.get("DTR_DB_HOST", "127.0.0.1")
    db_port = os.environ.get("DTR_DB_PORT", "5438")
    create_db = os.environ.get("DTR_DB_CREATE", None)
    url = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    app.config[
        "SQLALCHEMY_DATABASE_URI"
    ] = url
    db.init_app(app)

    if create_db is not None and create_db == "true":
        #create database if it does not exists
        engine = create_engine(url)
        if not database_exists(engine.url):
            create_database(engine.url)
        else:
            # Connect to the database if exits
            engine.connect()

        with app.app_context():
            db.create_all()

            from .models import GlobalParameters
            params = db.session.query(GlobalParameters).first()
            if params is None:
                params = GlobalParameters(mode = Mode.ONLINE)
                db.session.add(params)
                db.session.commit()
            app.logger.debug("database tables have been created")
