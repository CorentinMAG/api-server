from __future__ import annotations

from ..constantes import Protocol
from .base import StrictBaseModel
from .credentials import CredentialsSchema


class TargetParametersCreate(StrictBaseModel):
    use_ssl: bool = True
    verify: bool = True


class TargetParametersUpdate(StrictBaseModel):
    use_ssl: bool | None = None
    verify: bool | None = None


class TargetCreate(StrictBaseModel):
    name: str
    protocol: Protocol
    host: str
    port: int
    credentials: CredentialsSchema | None = None
    parameters: TargetParametersCreate = TargetParametersCreate()


class TargetUpdate(StrictBaseModel):
    name: str | None = None
    protocol: Protocol | None = None
    host: str | None = None
    port: int | None = None
    credentials: CredentialsSchema | None = None
    parameters: TargetParametersUpdate | None = None
