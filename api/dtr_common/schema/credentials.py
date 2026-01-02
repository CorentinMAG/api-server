from pydantic import SecretStr, field_serializer
from .base import StrictBaseModel


class CredentialsSchema(StrictBaseModel):
    login: str
    password: SecretStr

    @field_serializer("password", when_used="always")
    def serialize_password(self, value: SecretStr, _info):
        if _info.context and _info.context.get("include_secrets"):
            return value.get_secret_value()
        return str(value)
