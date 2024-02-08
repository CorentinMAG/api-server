from __future__ import annotations
from pydantic import BaseModel
from .. import db
from .base import BaseModel as Base
import api.models.credentials as cred
from typing import cast

class Target(BaseModel, Base):
    id: int | None = None
    logicalName: str
    protocol: str
    hostname: str
    port: int
    bucket: str | None = None
    credentials: dict | None = None

    def __init__(self, **kwargs) -> None:
        dcredentials = cast(dict | None, kwargs.pop("credentials", None))
        if dcredentials is not None:
            credentials_type = cast(str, dcredentials.pop("type", "password"))
            ncredentials = cast(cred.Credentials, (cred, f"{credentials_type.capitalize()}Credentials"))
            ncredentials.upsert()

        super().__init__(**kwargs)
        self.credentials = ncredentials

    def upsert(self) -> int:
        conn = db.get_db()
        cur = conn.cursor()

        credential_id: int | None = None
        if self.credentials is not None:
            credential_id = self.credentials.upsert()

        if self.id:
            cur.execute(
                "UPDATE target SET logicalname = %s, hostname = %s, port = %s, credentialid = %s, bucket = %s, protocol = %s WHERE targetid = %s",
                (self.logicalName, self.hostname, self.port, credential_id, self.bucket, self.protocol, self.id)
            )
        else:
            cur.execute(
                "INSERT INTO target SET logicalname = %s, hostname = %s, port = %s, credentialid = %s, bucket = %s, protocol = %s RETURNING targetid",
                (self.logicalName, self.hostname, self.port, credential_id, self.bucket, self.protocol)
            )
            self.id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return self.id

    def delete(self) -> None:
        if self.id is None:
            return

        conn = db.get_db()
        cur = conn.cursor()

        cur.execute(
            "DELETE FROM login WHERE loginid = %s",
            (self.id)
        )
        conn.commit()
        cur.close()

        if self.credentials is not None:
            self.credentials.delete()

