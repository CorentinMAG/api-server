from __future__ import annotations

import os

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
        """Basic health check endpoint for Kubernetes readiness probes"""
        return {"status": "healthy", "service": "api-server"}

    @app.route("/health", methods=["GET"])
    def health():
        """Comprehensive health check with database connectivity"""
        from api.db import db
        from api.services.utils import db_retry

        @db_retry(total=2, initial_delay=0.5, max_delay=2)
        def check_database():
            """Check database connectivity with retry"""
            db.session.execute(db.text("SELECT 1"))
            return "healthy"

        try:
            db_status = check_database()
        except Exception as e:
            app.logger.error("Database health check failed: %s", str(e))
            db_status = "unhealthy"
            return {
                "status": "unhealthy",
                "service": "api-server",
                "checks": {"database": db_status, "error": str(e)},
            }, 503

        return {
            "status": "healthy",
            "service": "api-server",
            "version": os.environ.get("DTR_API_VERSION", "unknown"),
            "checks": {"database": db_status},
        }

    @app.route("/ready", methods=["GET"])
    def ready():
        """Kubernetes readiness probe - checks if service is ready to accept traffic"""
        from api.db import db
        from api.services.utils import db_retry

        @db_retry(total=2, initial_delay=0.5, max_delay=2)
        def check_readiness():
            """Check database readiness with retry"""
            db.session.execute(db.text("SELECT 1"))
            return True

        try:
            check_readiness()
            return {
                "status": "ready",
                "service": "api-server",
                "version": os.environ.get("DTR_API_VERSION", "unknown"),
            }
        except Exception as e:
            app.logger.warning("Readiness check failed: %s", str(e))
            return {"status": "not_ready", "service": "api-server", "error": str(e)}, 503

    @app.route("/metrics", methods=["GET"])
    def metrics():
        """Basic metrics endpoint for monitoring"""
        from api.db import db
        from api.models import TransferPolicy, TransferRequest
        from api.services.utils import db_retry

        @db_retry(total=2, initial_delay=0.5, max_delay=2)
        def collect_metrics():
            """Collect metrics with database retry"""
            total_requests = db.session.query(TransferRequest).count()
            total_policies = db.session.query(TransferPolicy).count()
            return total_requests, total_policies

        try:
            total_requests, total_policies = collect_metrics()
            return {
                "service": "api-server",
                "version": os.environ.get("DTR_API_VERSION", "unknown"),
                "metrics": {
                    "total_transfer_requests": total_requests,
                    "total_transfer_policies": total_policies,
                    "database_connections": "available",
                },
            }
        except Exception as e:
            app.logger.error("Metrics collection failed: %s", str(e))
            return {"service": "api-server", "error": "metrics_unavailable", "message": str(e)}, 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        response = e.get_response()
        app.logger.error(
            "HTTP Exception occurred",
            extra={
                "error_type": "http_exception",
                "description": e.description,
                "code": e.code,
                "endpoint": request.endpoint,
                "method": request.method,
                "path": request.path,
                "component": "api",
                "trace": True if IS_DEBUG else False,
            },
        )
        return response

    @app.errorhandler(NotFound)
    def handle_not_found_error(e: NotFound):
        url = request.url
        app.logger.error(
            "Resource not found",
            extra={
                "error_type": "not_found",
                "url": url,
                "endpoint": request.endpoint,
                "method": request.method,
                "path": request.path,
                "component": "api",
                "trace": True if IS_DEBUG else False,
            },
        )
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
        errors = e.errors()
        app.logger.error(
            "Validation error occurred",
            extra={
                "error_type": "validation_error",
                "validation_errors": errors,
                "endpoint": request.endpoint,
                "method": request.method,
                "path": request.path,
                "component": "api",
                "trace": True if IS_DEBUG else False,
            },
        )
        return {"errors": errors}, 400

    @app.errorhandler(Exception)
    def handle_exception(e: Exception):
        app.logger.error(
            "Unhandled exception occurred",
            extra={
                "error_type": "unhandled_exception",
                "error_class": e.__class__.__name__,
                "error_details": str(e),
                "endpoint": request.endpoint,
                "method": request.method,
                "path": request.path,
                "component": "api",
                "trace": True if IS_DEBUG else False,
            },
        )
        return {"error": "internal server error"}, 500

    # @app.before_request
    # def log_request():
    #     body = request.json if request.is_json else "NO BODY"
    #     app.logger.debug("headers: %s body: %s", dict(request.headers), body)

    from api.routes import v1

    app.register_blueprint(v1, url_prefix="/dtr/v1")

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    return app
