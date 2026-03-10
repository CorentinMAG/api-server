from __future__ import annotations

from ..constantes import ServerType
from .base import StrictBaseModel
from .credentials import CredentialsSchema


class ServerCreate(StrictBaseModel):
    name: str
    type: ServerType
    host: str
    port: int
    timeout: int = 40
    credentials: CredentialsSchema | None = None


class ServerUpdate(StrictBaseModel):
    name: str | None = None
    host: str | None = None
    port: int | None = None
    timeout: int | None = None
    credentials: CredentialsSchema | None = None
