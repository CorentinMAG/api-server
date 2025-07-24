from __future__ import annotations

from flask import Blueprint

from . import configure, mode, notifications, policies, requests, trigger, worker

v1 = Blueprint("api_v1", __name__)

# List of blueprints to register
_sub_blueprints = [
    configure.bp,
    mode.bp,
    policies.bp,
    requests.bp,
    notifications.bp,
    trigger.bp,
    worker.bp,
]

for _bp in _sub_blueprints:
    v1.register_blueprint(_bp)
