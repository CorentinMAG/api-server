from __future__ import annotations

from flask import Flask, current_app, request
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException, NotFound

from .exceptions import AppException


def register_error_handlers(app: Flask):
    app.register_error_handler(HTTPException, handle_http_exception)
    app.register_error_handler(NotFound, handle_not_found_error)
    app.register_error_handler(SQLAlchemyError, handle_sql_exception)
    app.register_error_handler(ValidationError, handle_validation_error)
    app.register_error_handler(AppException, handle_app_exceptions)
    app.register_error_handler(Exception, handle_exception)


def handle_http_exception(e: HTTPException):
    current_app.logger.error("HTTP Exception occurred: %s", e.description)
    return {"error": e.description}, e.code


def handle_not_found_error(e: NotFound):
    url = request.url
    current_app.logger.error("Resource not found: %s", url)
    return {"error": "requested url does not exist", "details": {"url": url}}, 404


def handle_sql_exception(e: SQLAlchemyError):
    error_name = e.__class__.__name__
    current_app.logger.error("Database error occurred (%s): %s", error_name, str(e))
    return {"error": str(e)}, 500


def handle_validation_error(e: ValidationError):
    current_app.logger.error("Validation error occurred: %s", e.errors())
    return e.json(), 500


def handle_app_exceptions(e: AppException):
    return {"error": e.message}, e.status_code


def handle_exception(e: Exception):
    error_name = e.__class__.__name__
    current_app.logger.error("Unhandled exception occurred (%s): %s", error_name, str(e))
    return {"error": str(e)}, 500
