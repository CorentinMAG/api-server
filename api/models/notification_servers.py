from __future__ import annotations
from pydantic import BaseModel
from .. import db

class NotificationServer(BaseModel):
    id: int | None = None
    name: str
    type: str
    host: str
    timeout: int | None = 40
    notificationType: str

    def commit(self) -> None:
        conn = db.get_db()
        cur = conn.cursor()

        if self.id:
            ## update record
            cur.execute(
                "UPDATE INTO NotificationServer SET name = %s, type = %s, host = %s, timeout = %d, notificationType = %s) WHERE id = %d",
                (self.name, self.type, self.host, self.timeout, self.notificationType, self.id)
            )
        else:
            ## create record
            cur.execute(
                "INSERT INTO NotificationServer (name, type, host, timeout, notificationType) VALUES (%s, %s, %s, %d, %s)",
                (self.name, self.type, self.host, self.timeout, self.notificationType)
            )
        conn.commit()
        cur.close()

