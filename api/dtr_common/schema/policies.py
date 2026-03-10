from __future__ import annotations

from ..constantes import Type
from .base import StrictBaseModel


class SourcePolicyCreate(StrictBaseModel):
    target: str
    path: str | None = None
    purge: bool = False
    pattern: str


class SourcePolicyUpdate(StrictBaseModel):
    target: str | None = None
    path: str | None = None
    purge: bool | None = None
    pattern: str | None = None


class KafkaParametersCreate(StrictBaseModel):
    topic: str
    replicas: int = 1
    partitions: int = 1


class ServerParametersCreate(StrictBaseModel):
    server: str
    parameters: list[KafkaParametersCreate]


class ServerParametersUpdate(StrictBaseModel):
    server: str | None = None
    parameters: list[KafkaParametersCreate] | None = None


class DestinationPolicyCreate(StrictBaseModel):
    target: str
    path: str | None = None
    bucket: str | None = None
    tmp_prefix: str | None = None
    final_prefix: str | None = None
    notifications: list[ServerParametersCreate] | None = None


class DestinationPolicyUpdate(StrictBaseModel):
    target: str | None = None
    path: str | None = None
    bucket: str | None = None
    tmp_prefix: str | None = None
    final_prefix: str | None = None
    notifications: list[ServerParametersUpdate] | None = None


class TransferPolicyParametersCreate(StrictBaseModel):
    max_retry: int | None = None
    retry_delay: int | None = None
    transfer_requests_history: int | None = None
    only_new_data: bool | None = None
    transfer_timeout: int | None = None


class TransferPolicyParametersUpdate(StrictBaseModel):
    max_retry: int | None = None
    retry_delay: int | None = None
    transfer_requests_history: int | None = None
    only_new_data: bool | None = None
    transfer_timeout: int | None = None


class TransferPolicyCreate(StrictBaseModel):
    name: str
    enabled: bool = True
    type: Type = Type.PERIODICAL
    src: SourcePolicyCreate
    dests: list[DestinationPolicyCreate]
    queue: str
    trigger: str | None = None
    parameters: TransferPolicyParametersCreate = TransferPolicyParametersCreate()


class TransferPolicyUpdate(StrictBaseModel):
    name: str | None = None
    enabled: bool | None = None
    type: Type | None = None
    queue: str | None = None
    trigger: str | None = None
    src: SourcePolicyUpdate | None = None
    dests: list[DestinationPolicyUpdate] | None = None
    parameters: TransferPolicyParametersUpdate | None = None
