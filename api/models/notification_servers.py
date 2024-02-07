from __future__ import annotations
from pydantic import BaseModel
from .base import BaseModel as Base
from .. import db

class NotificationServer(BaseModel, Base):
    id: int | None = None
    name: str
    type: str
    host: str
    timeout: int | None = 40
    notificationType: str

    def upsert(self) -> int:
        conn = db.get_db()
        cur = conn.cursor()

        if self.id:
            ## update record
            cur.execute(
                "UPDATE INTO NotificationServer SET name = %s, type = %s, host = %s, timeout = %s, notificationType = %s) WHERE notificationserverid = %s",
                (self.name, self.type, self.host, self.timeout, self.notificationType, self.id)
            )
        else:
            ## create record
            cur.execute(
                "INSERT INTO NotificationServer (name, type, host, timeout, notificationtype) VALUES (%s, %s, %s, %s, %s) RETURNING notificationserverid",
                (self.name, self.type, self.host, self.timeout, self.notificationType)
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
            "DELETE FROM NotificationServer WHERE notificationserverid = %s",
            (self.id)
        )
        conn.commit()
        cur.close()

