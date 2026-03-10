from __future__ import annotations

from .base import BaseAPI
import api.routes.v1
from flask import Blueprint

v1 = Blueprint("api_v1", __name__)
BaseAPI.register(v1)


__all__ = ["v1"]
