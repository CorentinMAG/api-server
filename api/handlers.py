from __future__ import annotations
from flask import request
from api.utils.utils import custom_app
from .app import DTRFlask
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException, NotFound
from .errors import AppGlobalParametersError
from urllib.parse import urlparse

def register_handlers(app: DTRFlask) -> None:
    register_error_handlers(app)

def register_error_handlers(app: DTRFlask) -> None:
    app.register_error_handler(HTTPException, handle_http_exception)
    app.register_error_handler(NotFound, handle_not_found_error)
    app.register_error_handler(SQLAlchemyError, handle_sql_exception)
    app.register_error_handler(AppGlobalParametersError, handle_global_parameters_error)
    app.register_error_handler(ValidationError, handle_validation_error)
    app.register_error_handler(Exception, handle_exception)


def handle_http_exception(e: HTTPException):
    custom_app().logger.error("HTTP Exception occurred: %s", e.description)
    return {"error": e.description}, e.code

def handle_not_found_error(e: NotFound):
    url = request.url
    custom_app().logger.error("Resource not found: %s", url)
    return {"error": "requested url does not exist", "details": {"url": url}}, 404

def handle_sql_exception(e: SQLAlchemyError):
    error_name = e.__class__.__name__
    custom_app().logger.error("Database error occurred (%s): %s", error_name, str(e))
    return {"error": str(e)}, 500

def handle_validation_error(e: ValidationError):
    custom_app().logger.error("Validation error occurred: %s", e.errors())
    return e.json(), 500

def handle_global_parameters_error(e: AppGlobalParametersError):
    custom_app().logger.warning(e.message)
    path = urlparse(request.url).path

    if path.endswith("trigger"):
        return {"configuration": {}, "pagination": {"page": 1, "per_page": 0, "total": 0, "pages": 1}, "policies": []}, 404
    elif path.endswith("worker") or path.endswith("notifications"):
        return {"request": {}}
    return "", 404

def handle_exception(e: Exception):
    error_name = e.__class__.__name__
    custom_app().logger.error("Unhandled exception occurred (%s): %s", error_name, str(e), exc_info=True)
    return {"error": str(e)}, 500