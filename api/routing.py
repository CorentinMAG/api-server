from flask import request, Blueprint
from .services.configuration import configure as set_configuration, unconfigure as del_configuration
from .services.mode import switch_mode, get_mode
from .services.policies import filter_policies
from .utils.common import parse_params
from sqlalchemy_pagination import paginate

bp = Blueprint("api", __name__, url_prefix= "/api")

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
    # delete all records from all tables (but transfer requests, based on the body) in the db
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
    # set DTR to offline mode if in online mode
    switch_mode("offline")
    return "", 200

@bp.route("/online", methods = ["POST"])
def online():
    # set DTR to online mode if in offline mode
    switch_mode("online")
    return "", 200

@bp.route("/status", methods = ["GET"])
def status():
    # return DTR status (online or offline)
    return {"mode": get_mode()}, 200

@bp.route("/policies", methods = ["GET"])
def policies():
    # list all transfer policies
    # we can filtrate by using query parameters
    # - type: (periodical / commanded)
    # - dataType: (file / folder)
    # - enabled: (true / false)
    # - src
    # - dest
    page = request.args.get("page", type=int, default=1)
    page_size = request.args.get("page_size", type=int, default=10)

    parsed_params = parse_params(request.args.to_dict())

    query = filter_policies(parsed_params)
    result = paginate(query, page = page, page_size = page_size)
    return {
        "policies": [p.to_dict() for p in result.items], 
        "page": page, 
        "page_size": page_size, 
        "total": result.total
        }, 200

@bp.route("/requests", methods = ["GET"])
def requests():
    params = request.args.to_dict()
    # TODO: list all transfer requests
    pass

@bp.route("/configuration/notifier", methods = ["GET"])
def notifier():
    # TODO: return notifier expected configuration 
    pass

@bp.route("/configuration/trigger", methods = ["GET"])
def trigger():
    # TODO: return trigger expected configuration (i.e all activated periodical transfer policies)
    pass

@bp.route("/configuration/worker", methods = ["GET"])
def worker():
    # TODO: return worker expected configuration
    pass