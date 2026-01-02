from pydantic import UUID4
import datetime
from .policies import TransferPolicySchema, DestinationPolicySchema
from .states import StateSchema
from .base import StrictBaseModel


class PeriodicalTransferRequestSchema(StrictBaseModel):
    filename: str
    size: float
    modified_at: datetime.datetime


class TriggerTransferRequestSchema(StrictBaseModel):
    policy: int
    files: list[PeriodicalTransferRequestSchema]


class CommandedTransferRequestSchema(StrictBaseModel):
    transfer_policy: str
    path: str
    uid: UUID4 | None = None
    timestamp: datetime.datetime | None = None


class TransferRequestSchema(StrictBaseModel):
    id: int
    filename: str
    start: datetime.datetime | None
    end: datetime.datetime | None
    uid: UUID4
    follows_from_task: str | None
    size: float | None
    next_retry_min_time: datetime.datetime | None
    policy: TransferPolicySchema
    states: list[StateSchema]
    created_at: datetime.datetime
    nb_retry: int
    download_rate: float | None
    upload_rate: float | None
    download_time: float | None
    upload_time: float | None
    dest: DestinationPolicySchema
    src_relative_path: str | None
