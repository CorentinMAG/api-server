from __future__ import annotations

from functools import wraps
from typing import Type

from flask import g, request
from pydantic import BaseModel, ValidationError

from api.utils.responses import error_response

"""Validation utilities for Flask routes."""

SchemaType = Type[BaseModel]


def validate_query(schema: SchemaType):
    """Decorator to validate *query-string* parameters against a Pydantic schema.

    The validated model instance is stored in ``flask.g.validated_query``.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):  # type: ignore[override]
            try:
                validated = schema(**request.args.to_dict())  # type: ignore[arg-type]
            except ValidationError as exc:
                # Centralised 400 response
                return error_response("invalid query parameters", exc.errors(), 400)
            g.validated_query = validated  # type: ignore[attr-defined]
            return fn(*args, **kwargs)

        return wrapper

    return decorator
