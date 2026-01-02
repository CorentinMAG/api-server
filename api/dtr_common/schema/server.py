from .base import StrictBaseModel
from .credentials import CredentialsSchema
from ..constantes import ServerType


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
