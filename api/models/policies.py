from __future__ import annotations
from pydantic import BaseModel
from .. import db
from .base import BaseModel as Base
from .queue import Queue
from .data_type import DataType

class DestinationPolicy(BaseModel, Base):
    pass

class SourcePolicy(BaseModel, Base):
    pass

class TransferPolicy(Base):
    logicalName: str
    transferRequestType: str
    queue: Queue
    dataType: DataType
    sourcePolicy: dict
    destinationPolicy: dict

    def __init__(self, **kwargs) -> None:
        queue_id = kwargs.pop("queueId")
        dataType_name = kwargs.pop("dataType")

        queue = 1

        source_policy_json = kwargs.pop("source_policy")
        destination_policy_json = kwargs.pop("destination_policy")

        source_policy = SourcePolicy(source_policy_json)
        destination_policy = DestinationPolicy(destination_policy_json)
        source_policy.upsert()
        destination_policy.upsert()

        kwargs["sourcePolicy"] = source_policy
        kwargs["destinationPolicy"] = destination_policy
        kwargs["queue"]
        super().__init__(**kwargs)
