from __future__ import annotations
from flask import request
from api.utils import custom_app
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from werkzeug.exceptions import HTTPException, NotFound
from .exception import AppException
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from api.app import DTRApp

def register_error_handlers(app: DTRApp) -> None:
    app.register_error_handler(HTTPException, handle_http_exception)
    app.register_error_handler(NotFound, handle_not_found_error)
    app.register_error_handler(SQLAlchemyError, handle_sql_exception)
    app.register_error_handler(ValidationError, handle_validation_error)
    app.register_error_handler(AppException, handle_app_exception)
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
    if isinstance(e, IntegrityError):
        custom_app().logger.error("database integrity error ! %s", str(e))
        code = 409
    else:
        custom_app().logger.error("Database error occurred (%s): %s", error_name, str(e))
        code = 500
    return {"error": str(e)}, code

def handle_validation_error(e: ValidationError):
    custom_app().logger.error("Validation error occurred: %s", e.errors())
    return e.json(), 422

def handle_app_exception(e: AppException):
    return {"error": e.message}, e.status_code

def handle_exception(e: Exception):
    error_name = e.__class__.__name__
    custom_app().logger.error("Unhandled exception occurred (%s): %s", error_name, str(e))
    return {"error": str(e)}, 500