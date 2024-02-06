import psycopg
import os
from flask import g

def get_db():
    if "db" not in g:
        g.db = psycopg.connect(
            dbname=os.environ["DTR_DB_NAME"],
			user=os.environ["DTR_DB_USER"],
            password=os.environ["DTR_DB_PASSWORD"],
            host=os.environ["DTR_DB_HOST"],
            port=os.environ["DTR_DB_PORT"]
            )
    return g.db

def close_db(e = None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)