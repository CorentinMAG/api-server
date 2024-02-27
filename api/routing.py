from flask import request, Blueprint
from .services.configuration import configure as set_configuration, unconfigure as del_configuration, create_policies
from .services.mode import switch_mode, get_mode
from .services.policies import filter_policies
from .services.requests import filter_requests, create_request, update_request
from common.utils import parse_params
from common.jsontypes import CreateRequestJson, FilterRequestParams, FilterPolicyParams, UpdateRequestJson
from typing import cast
from sqlalchemy_pagination import paginate
from .db import db
from .models import NotificationServer

bp = Blueprint("api", __name__, url_prefix= "/api/v1")

@bp.route("/configure", methods = ["POST"])
def configure():
    """
    delete the previous configuration and apply a new one
    """
    payload = request.json

    del_configuration(keep = ["transfer_requests"])
    set_configuration(payload)
    return "", 201

@bp.route("/configure", methods = ["DELETE"])
def unconfigure():
    """
    delete all records from all tables in the database
    we can specify in the body if we want to delete all transfer requests
    """

    if request.data:
        payload = request.json
        if payload["requests"] == True:
            del_configuration()
        else:
            del_configuration(keep=["transfer_requests"])
    del_configuration(keep = ["transfer_requests"])
    return "", 200

@bp.route("/offline", methods = ["POST"])
def offline():
    """
    set DTR to offline mode
    """
    switch_mode("offline")
    return "", 200

@bp.route("/online", methods = ["POST"])
def online():
    """
    set DTR to online mode
    """

    switch_mode("online")
    return "", 200

@bp.route("/status", methods = ["GET"])
def status():
    """
    return DTR status
    """

    params = get_mode()
    return params.to_dict(), 200

@bp.route("/policies", methods = ["GET"])
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

    page = request.args.get("page", type=int, default=1)
    page_size = request.args.get("page_size", type=int, default=10)

    parsed_params = cast(FilterPolicyParams, parse_params(request.args.to_dict()))

    query = filter_policies(parsed_params)
    result = paginate(query, page = page, page_size = page_size)
    return {
        "policies": [p.to_dict(rules=("-transfers.policy",)) for p in result.items], 
        "page": page, 
        "page_size": page_size, 
        "total": result.total
        }, 200

@bp.route("/policies", methods = ["POST"])
def create_policies():
    # TODO: create policies programatically
    payload = request.json
    policies = payload["policies"]
    create_policies(policies)

@bp.route("/requests", methods = ["GET"])
def requests():
    """
    list all transfer requests
    output can be filtered by using query params
    - state: queued / completed / failed / in_progress
    - queues: name1,name2,...
    """

    page = request.args.get("page", type=int, default=1)
    page_size = request.args.get("page_size", type=int, default=10)

    parsed_params = cast(FilterRequestParams, parse_params(request.args.to_dict()))

    query = filter_requests(parsed_params)
    result = paginate(query, page = page, page_size = page_size)

    return {
        "requests": [r.to_dict(rules=("-policy.transfers",)) for r in result.items],
        "page": page,
        "page_size": page_size,
        "total": result.total
    }, 200

@bp.route("/requests", methods = ["POST"])
def new_requests():
    payload: CreateRequestJson = request.json

    files = payload["files"]
    policy_id = payload["policy"]

    create_request(policy_id, files)
    return "", 201

@bp.route("/requests", methods = ["PUT"])
def update_requests():
    payload: UpdateRequestJson = request.json

    request_id = payload["request_id"]
    status = payload["status"]
    reason = payload.get("reason", None)

    update_request(request_id, status, reason)
    return "", 200


@bp.route("/configuration/notifier", methods = ["GET"])
def notifier():
    """
    return server configuration
    """
    servers = db.session.query(NotificationServer).all()
    return [s.to_dict(only=("name", "type", "host", "port", "timeout", "credentials")) for s in servers]

@bp.route("/notification", methods = ["GET"])
def notification():
    page = request.args.get("page", type=int, default=1)
    page_size = request.args.get("page_size", type=int, default=10)

    params = {
        "state": "notify"
    }

    query = filter_requests(params)
    result = paginate(query, page = page, page_size = page_size)

    return {
        "requests": [r.to_dict(rules=("-policy.transfers",)) for r in result.items],
        "page": page,
        "page_size": page_size,
        "total": result.total
    }, 200

@bp.route("/configuration/trigger", methods = ["GET"])
def trigger():
    """
    return trigger configuration
    i.e all activated periodical transfer policies
    """

    page = request.args.get("page", type=int, default=1)
    page_size = request.args.get("page_size", type=int, default=10)
    params = {
        "enabled": True,
        "type": "periodical"
    }
    query = filter_policies(params)
    result = paginate(query, page = page, page_size = page_size)
    return {
        "policies": [p.to_dict() for p in result.items], 
        "page": page, 
        "page_size": page_size, 
        "total": result.total
        }, 200

@bp.route("/configuration/worker", methods = ["GET"])
def worker():
    # TODO: return worker expected configuration
    pass