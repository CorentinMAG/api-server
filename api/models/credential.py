from __future__ import annotations
from pydantic import BaseModel
from .base import BaseModel as Base
from .. import db


class Credentials(Base):
    pass
    

class PasswordCredentials(Credentials, BaseModel):
    id: int | None = None
    login: str
    password: str

    def upsert(self) -> int:
        conn = db.get_db()
        cur = conn.cursor()

        if self.id:
            cur.execute(
                "UPDATE login SET login = %s, password = %s WHERE loginid = %s",
                (self.login, self.password, self.id)
            )
        else:
            cur.execute(
                "INSERT INTO login (login, password) VALUES (%s, %s) RETURNING loginid",
                (self.login, self.password)
            )
            self.id = cur.fetchone()[0]

            cur.execute(
                "INSERT INTO credential (loginid, credentialtype) VALUES (%s, %s)",
                (self.id, "password")
            )
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
        cur.execute(
            "DELETE FROM credential WHERE loginid = %s",
            (self.id)
        )
        conn.commit()
        cur.close()