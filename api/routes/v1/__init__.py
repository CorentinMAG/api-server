from __future__ import annotations

from flask import Blueprint
from api.utils import check_server_configured, check_offline_mode_v2

from .parameters import bp as parameters_bp
from .targets import bp as target_bp
from .policies import bp as policy_bp
from .queues import bp as queue_bp
from .servers import bp as server_bp


def register_blueprints(node: Blueprint, bps: list[Blueprint]) -> None:
    for bp in bps:
        node.register_blueprint(bp)


v1 = Blueprint("api_v1", __name__)


v1_no_check = Blueprint("no_check", __name__)
v1_check = Blueprint("check", __name__)
v1_check.before_request(check_offline_mode_v2)
v1_check.before_request(check_server_configured)

no_check_bps = [
    # configure.bp
    parameters_bp
]

check_bps = [
    policy_bp,
    queue_bp,
    target_bp,
    server_bp,
    # policies.bp
    # requests.bp
    # notifications.bp
    # trigger.bp
    # worker.bp
]

register_blueprints(v1_check, check_bps)
register_blueprints(v1_no_check, no_check_bps)
register_blueprints(v1, [v1_no_check, v1_check])
