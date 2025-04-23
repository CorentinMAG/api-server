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
        app.logger.error(
            "HTTP Exception occurred",
            extra={
                'error_type': 'http_exception',
                'description': e.description,
                'code': e.code,
                'endpoint': request.endpoint,
                'method': request.method,
                'path': request.path,
                'component': 'api',
                'trace': True if is_debug else False
            }
        )
        return response

    @app.errorhandler(NotFound)
    def handle_not_found_error(e: NotFound):
        url = request.url
        app.logger.error(
            "Resource not found",
            extra={
                'error_type': 'not_found',
                'url': url,
                'endpoint': request.endpoint,
                'method': request.method,
                'path': request.path,
                'component': 'api',
                'trace': True if is_debug else False
            }
        )
        return {"error": "requested url does not exist", "details": {"url": url}}, 404

    @app.errorhandler(SQLAlchemyError)
    def handle_sql_exception(e: SQLAlchemyError):
        app.logger.error(
            "Database error occurred",
            extra={
                'error_type': 'database_error',
                'error_details': str(e),
                'endpoint': request.endpoint,
                'method': request.method,
                'path': request.path,
                'component': 'api',
                'trace': True if is_debug else False
            }
        )
        return {"error": "database error occurred"}, 500

    @app.errorhandler(ValidationError)
    def handle_validation_error(e: ValidationError):
        errors = e.errors()
        app.logger.error(
            "Validation error occurred",
            extra={
                'error_type': 'validation_error',
                'validation_errors': errors,
                'endpoint': request.endpoint,
                'method': request.method,
                'path': request.path,
                'component': 'api',
                'trace': True if is_debug else False
            }
        )
        return {"errors": errors}, 400

    @app.errorhandler(Exception)
    def handle_exception(e: Exception):
        app.logger.error(
            "Unhandled exception occurred",
            extra={
                'error_type': 'unhandled_exception',
                'error_class': e.__class__.__name__,
                'error_details': str(e),
                'endpoint': request.endpoint,
                'method': request.method,
                'path': request.path,
                'component': 'api',
                'trace': True if is_debug else False
            }
        )
        return {"error": "internal server error"}, 500

    # @app.before_request
    # def log_request():
    #     body = request.json if request.is_json else "NO BODY"
    #     app.logger.debug("headers: %s body: %s", dict(request.headers), body)

    from api.routes import v1

    app.register_blueprint(v1, url_prefix="/dtr/v1")

    from . import db

    db.init_app(app)

    return app
