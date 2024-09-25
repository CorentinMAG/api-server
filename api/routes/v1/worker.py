from flask import Blueprint, request
from api.services.filters import get_params
from dtr_common.constantes import Mode, State as StateEnum
from api.models import State
from api.db import db
from api.services.requests import get_next_request

bp = Blueprint("worker", __name__)


@bp.route("configuration/worker", methods=["GET"])
def worker():
    nglobal_parameters = get_params()
    if nglobal_parameters is None or nglobal_parameters.mode == Mode.OFFLINE:
        return {
            "request": {},
        }
    else:
        session = db.session
        worker_storage = request.args.get("worker_storage")
        params = {"worker_storage": worker_storage}
        next_request = get_next_request(session, params)
        if next_request is not None:
            nstate = State(state=StateEnum.IN_PROGRESS.value.upper())
            next_request.states.append(nstate)
            db.session.commit()
            return {"request": next_request.to_dict(rules=("-policy.transfers",))}, 200
        return {"request": []}, 200
