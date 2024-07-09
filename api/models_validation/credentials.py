from pydantic import BaseModel, ConfigDict


class CredentialsModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    login: str
    password: str
    token: str | None
    type: str
    target_id: int | None
    server_id: int | None
