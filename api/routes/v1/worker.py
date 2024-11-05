from flask import Blueprint, request
from api.services.filters import get_params
from dtr_common.constantes import Mode, State as StateEnum
from api.models import State
from api.db import db
from api.services.requests import get_next_request
import datetime

bp = Blueprint("worker", __name__)


@bp.route("configuration/worker", methods=["GET"])
def worker():
    ngparams = get_params()
    if ngparams is None or ngparams.mode == Mode.OFFLINE:
        return {"request": None}
    else:
        worker_storage = request.args.get("size", type=float)
        params = {"size": worker_storage, "state": StateEnum.QUEUED}
        next_request = get_next_request(params)
        if next_request is not None:
            nstate = State(state=StateEnum.IN_PROGRESS)
            next_request.states.append(nstate)
            next_request.start = datetime.datetime.now(datetime.timezone.utc)
            db.session.commit()
            return {"request": next_request.to_dict()}, 200
        return {"request": None}, 200
