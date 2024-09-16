from flask import Blueprint
from api.services.filters import get_params
from dtr_common.constantes import Mode, State as StateEnum
from api.models import State
from api.db import db
from api.services.requests import get_next_request
import os

bp = Blueprint("worker", __name__)

DTR_WORKER_SIZE = os.environ.get("DTR_WORKER_SIZE:", "20G")


@bp.route("configuration/worker", methods=["GET"])
def worker():
    nglobal_parameters = get_params()
    if nglobal_parameters is None or nglobal_parameters.mode == Mode.OFFLINE:
        return {
            "request": {},
        }
    else:
        session = db.session
        params = {"worker_size": f"{DTR_WORKER_SIZE}"}
        request = get_next_request(session, params)
        if request is not None:
            nstate = State(state=StateEnum.IN_PROGRESS.value.upper())
            request.states.append(nstate)
            db.session.commit()
            return {"request": request.to_dict(rules=("-policy.transfers",))}, 200
        return {"request": []}, 200
