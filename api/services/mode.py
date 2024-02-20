from ..models import GlobalParameters
from ..db import db
from flask import current_app as app

def switch_mode(mode: str) -> None:
    params = db.session.query(GlobalParameters).first()
    if params is None:
        app.logger.error("no global parameters, the DTR doesn't know how to switch mode")
    else:
        params.mode = mode
        db.session.commit()

def get_mode() -> GlobalParameters:
    params = db.session.query(GlobalParameters).first()
    if params is None:
        app.logger.error("no global parameters, the DTR doesn't know how to fetch the mode")
    else:
        return params