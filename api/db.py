import os
from flask import Flask
from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy


class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class = Base)

def init_app(app: Flask):
    app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql+psycopg://{os.environ['DTR_DB_USER']}:{os.environ['DTR_DB_PASSWORD']}@{os.environ['DTR_DB_HOST']}/{os.environ['DTR_DB_NAME']}"
    db.init_app(app)
    with app.app_context():
        db.create_all()
    