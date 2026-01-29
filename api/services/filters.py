# from __future__ import annotations

# from flask import current_app as app
# from api.models import db
# from ..models import GlobalParameters
# from .utils import transactional
# from sqlalchemy import select

# @transactional
# def switch_mode(mode: str) -> None:
#     params = db.session.query(GlobalParameters).first()
#     if params is None:
#         app.logger.error("no global parameters, the dtr doesn't know how to switch mode")
#     else:
#         params.mode = mode
#         app.logger.info("dtr has switched to %s mode", mode.value.upper())


# def get_params() -> GlobalParameters | None:
#     stmt = select(GlobalParameters).limit(1)
#     nparams = db.session.execute(stmt).scalar()
#     if nparams:
#         return nparams
#     else:
#         app.logger.warning(f"Could not retrieve global parameters")
