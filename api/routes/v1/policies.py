from flask import Blueprint, request
from api.services.filters import get_params
from dtr_common.constantes import Mode
from typing import cast
from dtr_common.types.filter import FilterPolicyParams
from dtr_common.types.requests import CreatePoliciesJson
from dtr_common.utils import parse_params
from api.services.policies import filter_policies
from api.services.configuration import create_policies
from sqlalchemy_pagination import paginate

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

    nglobal_parameters = get_params()

    if nglobal_parameters is None or nglobal_parameters.mode == Mode.OFFLINE:
        return {"policies": [], "page": 0, "page_size": 0, "total": -1}

    page = request.args.get("page", type=int, default=1)
    page_size = request.args.get("page_size", type=int, default=10)

    parsed_params = cast(FilterPolicyParams, parse_params(request.args.to_dict()))

    query = filter_policies(parsed_params)
    result = paginate(query, page=page, page_size=page_size)
    return {
        "policies": [p.to_dict(rules=("-transfers.policy",)) for p in result.items],
        "page": page,
        "page_size": page_size,
        "total": result.total,
    }, 200


@bp.route("/policies", methods=["POST"])
def post_policies():
    payload: CreatePoliciesJson = request.json  # --check-untyped-defs
    policies = payload["policies"]
    create_policies(policies)

    return "", 201
