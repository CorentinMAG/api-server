from flask import Blueprint, request
from api.services.filters import get_params
from dtr_common.constantes import Mode
from typing import cast
from dtr_common.utils import parse_params
from api.services.policies import filter_policies, update_policy
from api.services.configuration import create_policies
from api.db import db
from api.models import TransferPolicy

bp = Blueprint("policies", __name__)


@bp.route("/policies", methods=["GET"])
def policies():
    """
    list all transfer policies.
    output can be filtered by using query params:
    - id: int
    - ids: str
    - type: periodical / commanded
    - dataType: file / folder
    - enabled: true / false
    - queues: name1,name2,...
    - src
    - dest
    """

    ngparams = get_params()

    if ngparams is None or ngparams.mode == Mode.OFFLINE:
        return {"policies": [], "page": 0, "page_size": 0, "total": -1}

    page = request.args.get("page", type=int, default=1)
    page_size = request.args.get("page_size", type=int, default=10)

    parsed_params = parse_params(request.args.to_dict())

    query = filter_policies(parsed_params)
    result = db.paginate(query, page=page, per_page=page_size)
    policies = cast(list[TransferPolicy], result.items)
    return {
        "policies": [p.to_dict() for p in policies],
        "page": page,
        "page_size": page_size,
        "total": result.total,
    }, 200


@bp.route("/policies", methods=["POST"])
def post_policies():
    payload = request.json
    policies = payload["policies"]
    create_policies(policies)

    return "", 201


@bp.route("policies/<int:id>", methods=["PUT"])
def put_policy(id: int):
    payload = request.json

    update_policy(id, payload)
    return "", 204
