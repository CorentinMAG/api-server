from flask import current_app as app

from ..db import db
from ..models import GlobalParameters


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
        raise Exception()
    else:
        return params
