from __future__ import annotations

from flask import Blueprint

from . import configure, mode, notifications, policies, requests, trigger, worker

v1 = Blueprint("api_v1", __name__)

v1.register_blueprint(configure.bp)
v1.register_blueprint(mode.bp)
v1.register_blueprint(policies.bp)
v1.register_blueprint(requests.bp)
v1.register_blueprint(notifications.bp)
v1.register_blueprint(trigger.bp)
v1.register_blueprint(worker.bp)
