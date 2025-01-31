import os

from flask import Flask, request
from werkzeug.exceptions import HTTPException, NotFound
from pydantic import ValidationError


from dtr_common.logs.logger import create_logger
from sqlalchemy.exc import SQLAlchemyError


def create_app():
    app = Flask(__name__, instance_relative_config=False)

    log_lvl = os.environ.get("DTR_LOG_LEVEL", "INFO")
    is_debug = log_lvl == "DEBUG"
    version = os.environ["DTR_API_VERSION"]
    ssystem_version = os.environ["DTR_VERSION"]

    app.logger = create_logger("api", log_lvl, version, "dtr", ssystem_version)

    @app.route("/", methods=["GET"])
    def index():
        return {"message": "DTR api-server entrypoint"}

    @app.route("/healthz", methods=["GET"])
    def healthz():
        return {"message": "healthy"}

    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        response = e.get_response()
        app.logger.error(e.description, stack_info=is_debug, exc_info=is_debug)
        return response

    @app.errorhandler(NotFound)
    def handle_not_found_error(e: NotFound):
        url = request.url
        app.logger.error("request url: %s does not exist", url, stack_info=is_debug, exc_info=is_debug)
        return {"error": "requested url does not exist", "details": {"url": url}}

    @app.errorhandler(SQLAlchemyError)
    def handle_sql_exception(e: SQLAlchemyError):
        app.logger.error(e, stack_info=is_debug, exc_info=is_debug)
        return "", 500

    @app.errorhandler(ValidationError)
    def handle_validation_error(e: ValidationError):
        app.logger.error("Validation error: %s", e.errors(), stack_info=is_debug, exc_info=is_debug)
        return {"errors": e.errors()}, 500

    @app.errorhandler(Exception)
    def handle_exception(e: Exception):
        app.logger.error(e, stack_info=is_debug, exc_info=is_debug)
        return {"error": str(e)}

    # @app.before_request
    # def log_request():
    #     body = request.json if request.is_json else "NO BODY"
    #     app.logger.debug("headers: %s body: %s", dict(request.headers), body)

    from api.routes import v1

    app.register_blueprint(v1, url_prefix="/api/v1")

    from . import db

    db.init_app(app)

    return app
