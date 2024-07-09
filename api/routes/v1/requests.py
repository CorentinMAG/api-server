from flask import Blueprint, request
from typing import cast
from api.services.filters import get_params
from api.services.requests import filter_requests, create_request, update_request
from dtr_common.constantes import Mode
from dtr_common.utils import parse_params
from dtr_common.types.filter import FilterRequestParams
from dtr_common.types.requests import CreateRequestJson, UpdateRequestJson
from sqlalchemy_pagination import paginate

bp = Blueprint("requests", __name__)


@bp.route("/requests", methods=["GET"])
def requests():
    """
    list all transfer requests
    output can be filtered by using query params
    - state: queued / sucessful / failed / in_progress
    - queues: name1,name2,...
    """

    nglobal_parameters = get_params()
    if nglobal_parameters.mode == Mode.OFFLINE:
        return {
            "requests": [],
            "page": 0,
            "page_size": 0,
            "total": -1,
        }
    elif nglobal_parameters.mode == Mode.OFFLINE:
        return {"requests": [], "page": 0, "page_size": 0, "total": -1}
    else:
        page = request.args.get("page", type=int, default=1)
        page_size = request.args.get("page_size", type=int, default=10)

        parsed_params = cast(FilterRequestParams, parse_params(request.args.to_dict()))

        query = filter_requests(parsed_params)
        result = paginate(query, page=page, page_size=page_size)

        return {
            "requests": [r.to_dict(rules=("-policy.transfers",)) for r in result.items],
            "page": page,
            "page_size": page_size,
            "total": len(result.items),
        }, 200


@bp.route("/requests", methods=["POST"])
def new_requests():
    payload: CreateRequestJson = request.json

    files = payload["dict_files"]
    policy_id = payload["policy"]

    create_request(policy_id, files)
    return "Request successffully created", 201


@bp.route("/requests", methods=["PUT"])
def update_requests():
    payload: UpdateRequestJson = request.json

    request_id = payload["request_id"]
    status = payload["status"]
    sub_status = payload.get("sub_status", None)
    failure_reason = payload.get("failure_reason", None)
    nb_retry = payload.get("nb_retry", 0)
    next_retry_min_time = payload.get("next_retry_min_time", None)

    update_request(request_id, status, sub_status, next_retry_min_time, nb_retry, failure_reason)
    return "", 200
