from __future__ import annotations
from typing import cast

from flask import current_app, request

from api.app import DTRApp
from api.dtr_common.constantes import Mode
from typing import Callable
from functools import wraps


def custom_app() -> DTRApp:
    return cast(DTRApp, current_app)


def check_offline_mode(f: Callable) -> Callable:
    @wraps(f)
    def wrapper(*args, **kwargs):
        response = check_offline_mode_v2()
        if response:
            return response
        return f(*args, **kwargs)

    return wrapper


def check_offline_mode_v2(
    offline_response: dict[str, any] | None = None, status_code: int = 404
):
    from api.services.base import BaseService
    from api.services.parameters import GlobalParametersService

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
            return None
    return {"message": "DTR is not configured yet"}, 500
