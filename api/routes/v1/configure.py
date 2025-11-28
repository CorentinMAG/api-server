"""
Configuration API routes with dependency injection and error handling.
"""

from __future__ import annotations

from dtr_common.schema import ConfigurationSchema
from flask import Blueprint, current_app as app, request

from api.services.configuration import configure as set_configuration, unconfigure as del_configuration

bp = Blueprint("configuration", __name__)


@bp.route("/configure", methods=["POST"])
def configure():
    """
    delete the previous configuration and apply a new one
    """
    payload = request.json

    if not payload:
        return
    configuration = ConfigurationSchema(**payload)
    set_configuration(configuration)
    app.logger.info("New configuration has been successfully applied")
    return {"message": "new configuration has been applied"}, 201


@bp.route("/configure", methods=["DELETE"])
def unconfigure():
    """
    delete all records from all tables in the database
    we can specify in the body if we want to delete all transfer requests
    """
    del_configuration(keep=["transfer_requests", "states"])
    app.logger.info("configuration has been successfully deleted")
    return {"message": "configuration has been deleted"}, 200
