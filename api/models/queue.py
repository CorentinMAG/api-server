from __future__ import annotations
from pydantic import BaseModel
from .. import db
from .base import BaseModel as Base


class Queue(BaseModel, Base):
    id: int | None = None
    maxQueuedItems: int
    priorityOrder: int

    def upsert(self) -> int:
        conn = db.get_db()
        cur = conn.cursor()

        if self.id:
            cur.execute(
                "UPDATE INTO queue SET maxqueueditems = %s, priorityorder = %s WHERE queueid = %s",
                (self.maxQueuedItems, self.priorityOrder, self.id)
            )
        else:
            cur.execute(
                "INSERT INTO queue (maxqueueditems, priorityorder) VALUES (%s, %s) RETURNING queueid",
                (self.maxQueuedItems, self.priorityOrder)
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
            "DELETE FROM queue WHERE queuid = %s",
            (self.id)
        )
        conn.commit()
        cur.close()
