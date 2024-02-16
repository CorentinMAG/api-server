from flask import request, Blueprint
from .services.configuration import configure as set_configuration

bp = Blueprint("api", __name__, url_prefix= "/api")


@bp.route("/configure", methods = ["POST"])
def configure():
    payload = request.json
    set_configuration(payload)
    return "", 201

@bp.route("/configure", methods = ["DELETE"])
def unconfigure():
    payload = request.json
    # TODO: delete all records (but transfer requests, based on the body) in the db
    pass

@bp.route("/offline", methods = ["POST"])
def offline():
    # TODO: set DTR to offline mode if in online mode
    pass

@bp.route("/online", methods = ["POST"])
def online():
    # TODO: set DTR to online mode if in offline mode
    pass

@bp.route("/status", methods = ["GET"])
def status():
    # TODO: return DTR status (online or offline)
    pass

@bp.route("/policies", methods = ["GET"])
def policies():
    params = request.args.to_dict()
    # TODO: list all transfer policies
    pass

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