from flask import request, Blueprint, current_app as app
from api.services.configuration import configure as set_configuration, unconfigure as del_configuration
from sqlalchemy.exc import SQLAlchemyError
from dtr_common.schema import ConfigurationSchema

bp = Blueprint("configuration", __name__)


@bp.route("/configure", methods=["POST"])
def configure():
    """
    delete the previous configuration and apply a new one
    """
    payload = request.json

    del_configuration(keep=["transfer_requests", "global_parameters", "states"])

    configuration = ConfigurationSchema(**payload)

    try:
        set_configuration(configuration)
        app.logger.info("new configuration has been succesfully applied")
        return {"message": "configuration has been applied"}, 201
    except Exception as e:
        raise SQLAlchemyError(e)


@bp.route("/configure", methods=["DELETE"])
def unconfigure():
    """
    delete all records from all tables in the database
    we can specify in the body if we want to delete all transfer requests
    """
    del_configuration(keep=["transfer_requests"])
    app.logger.info("configuration has been successfully deleted")
    return {"message": "configuration has been deleted"}, 200
