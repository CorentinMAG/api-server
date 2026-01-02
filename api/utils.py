from flask import current_app
from functools import wraps
from api.app import DTRApp
from typing import cast
from api.dtr_common.constantes import Mode


def custom_app() -> DTRApp:
    return cast(DTRApp, current_app)


def check_server_configured():
    """check if server is configure or not"""
    from api.routes import BaseAPI

    service = BaseAPI._get_or_create_service("GlobalParameterService")
    parameters = service.get()
    if not parameters:
        return {"message": "DTR is not configured yet"}, 500


def check_offline_mode_v2(
    offline_response: dict[str, any] | None = None, status_code: int = 404
):
    from api.routes import BaseAPI

    service = BaseAPI._get_or_create_service("GlobalParameterService")
    params = service.get()
    if params:
        is_offline = params.mode
        if is_offline == Mode.OFFLINE:
            if offline_response:
                return offline_response, status_code
            return {
                "status": "offline",
                "message": "API is currently offline",
                "error": "Service temporarily unavailable",
            }, status_code


def check_offline_mode(offline_response: dict | None = None, status_code: int = 404):
    """Decorator to check if the server is in offline mode."""
    from api.routes import BaseAPI

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            service = BaseAPI._get_or_create_service("GlobalParameterService")
            params = service.get()
            if params:
                is_offline = params.mode
                if is_offline == Mode.OFFLINE:
                    if offline_response:
                        return offline_response, status_code
                    return {
                        "status": "offline",
                        "message": "API is currently offline",
                        "error": "Service temporarily unavailable",
                    }, status_code
            return f(*args, **kwargs)
