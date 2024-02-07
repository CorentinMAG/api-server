from __future__ import annotations
from pydantic import BaseModel
from .. import db
from .base import BaseModel as Base


class TransferPolicy(BaseModel, Base):
    pass