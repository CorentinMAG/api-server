"""Standardised JSON response helpers."""
from __future__ import annotations

from typing import Any

from flask import jsonify


def success_response(data: Any | None = None, status_code: int = 200):
    payload: dict[str, Any] = {"success": True}
    if data is not None:
        payload["data"] = data
    response = jsonify(payload)
    response.status_code = status_code
    return response


def error_response(message: str, details: Any | None = None, status_code: int = 400):
    payload: dict[str, Any] = {
        "success": False,
        "error": {
            "message": message,
            "details": details,
        },
    }
    response = jsonify(payload)
    response.status_code = status_code
    return response
