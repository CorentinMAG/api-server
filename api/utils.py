from flask import current_app, request
from functools import wraps
from api.app import DTRApp
from typing import cast
from dtr_common.constantes import Mode


def custom_app() -> DTRApp:
    return cast(DTRApp, current_app)

def check_offline_mode(offline_response: dict | None = None, status_code: int = 404):
    """Decorator to check if the server is in offline mode."""
    from api.services import BaseService, GlobalParametersService
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            service = BaseService._get_or_create_service(GlobalParametersService)
            params = service.get()
            if params:
                is_offline = params.mode
                if is_offline == Mode.OFFLINE and request.method == "GET":
                    if offline_response:
                        return offline_response, status_code
                    return {
                        "status": "offline",
                        "message": "API is currently offline",
                        "error": "Service temporarily unavailable",
                    }, status_code
                else:
                    return f(*args, **kwargs)
            else:
                return {"error": "DTR is not configured yet"}, 500
        return wrapper
    return decorator


def route(url: str, methods: dict| None = None):
    """
    this decorator can be used to add metadata to a method
    The BaseAPI class will then register the route
    """
    if methods is None:
        methods = ["GET"]
    def decorator(f):
        f._route = {
            "path": url,
            "methods": methods
        }
        return f
    return decorator