from __future__ import annotations
from pydantic import BaseModel
from .. import db
from .base import BaseModel as Base

class GlobalParameters(BaseModel, Base):
    databaseRetentionDays: int
    maxRetry: int
    retryDelaySeconds: int
    queueMaxItems: int
    queueThreshold: int
    notificationPollingInterval: int

    def upsert(self) -> int:
        return 1

    def delete(self) -> None:
        pass



