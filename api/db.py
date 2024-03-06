import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


def init_app(app: Flask):
    db_user = os.environ["DTR_DB_USER"]
    db_password = os.environ["DTR_DB_PASSWORD"]
    db_name = os.environ["DTR_DB_NAME"]
    db_host = os.environ["DTR_DB_HOST"]
    db_port = os.environ["DTR_DB_PORT"]
    create_db = os.environ.get("DTR_DB_CREATE", None)
    app.config[
        "SQLALCHEMY_DATABASE_URI"
    ] = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    db.init_app(app)

    if create_db is not None and create_db == "true":
        from .models.parameters import GlobalParameters
        from common.constantes import Mode

        with app.app_context():
            db.create_all()
            param = GlobalParameters(mode=Mode.ONLINE)
            db.session.add(param)
            db.session.commit()
