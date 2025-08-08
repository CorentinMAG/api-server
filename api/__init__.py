from __future__ import annotations
from flask import Flask, request
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException, NotFound

from config import IS_DEBUG, logger

from .db import db, init_app as init_db_app


def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.logger = logger

    # Initialize extensions
    init_db_app(app)

    @app.route("/", methods=["GET"])
    def index():
        return {"message": "DTR api-server entrypoint"}

    @app.route("/healthz", methods=["GET"])
    def healthz():
        """
        Basic health check endpoint for Kubernetes readiness probes
        """
        return {"status": "healthy", "service": "api-server"}

    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        app.logger.error("HTTP Exception occurred: %s", e.description)
        return {"error": e.description}, e.code

    @app.errorhandler(NotFound)
    def handle_not_found_error(e: NotFound):
        url = request.url
        app.logger.error("Resource not found: %s", url)
        return {"error": "requested url does not exist", "details": {"url": url}}, 404

    @app.errorhandler(SQLAlchemyError)
    def handle_sql_exception(e: SQLAlchemyError):
        from sqlalchemy.exc import DisconnectionError, OperationalError, TimeoutError

        # Check if this is a connection-related error
        is_connection_error = isinstance(e, (OperationalError, DisconnectionError, TimeoutError))

        error_details = {
            "error": "database error occurred",
            "type": "connection_error" if is_connection_error else "database_error",
        }

        if is_connection_error:
            app.logger.error(
                "Database connection error occurred",
                extra={
                    "error_type": "database_connection_error",
                    "error_details": str(e),
                    "endpoint": request.endpoint,
                    "method": request.method,
                    "path": request.path,
                    "component": "api",
                    "trace": True if IS_DEBUG else False,
                },
            )
            error_details["message"] = "Database is temporarily unavailable. Please try again later."
            return error_details, 503  # Service Unavailable
        else:
            app.logger.error(
                "Database error occurred",
                extra={
                    "error_type": "database_error",
                    "error_details": str(e),
                    "endpoint": request.endpoint,
                    "method": request.method,
                    "path": request.path,
                    "component": "api",
                    "trace": True if IS_DEBUG else False,
                },
            )
            return error_details, 500

    @app.errorhandler(ValidationError)
    def handle_validation_error(e: ValidationError):
        app.logger.error("Validation error occurred: %s", e.errors())
        return e.json(), 500

    @app.errorhandler(Exception)
    def handle_exception(e: Exception):
        error_name = e.__class__.__name__
        app.logger.error("Unhandled exception occurred (%s): %s", error_name, str(e))
        return {"error": str(e)}, 500

    from api.routes import v1

    app.register_blueprint(v1, url_prefix="/dtr/v1")

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    return app
