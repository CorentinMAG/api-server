from __future__ import annotations
from pydantic import BaseModel
from .base import BaseModel as Base
from .. import db

class DataType(BaseModel, Base):
    id: int | None = None
    logicalName: str
    description: str | None = None
    itemType: str

    def upsert(self) -> int:
        conn = db.get_db()
        cur = conn.cursor()

        if self.id:
            ## update record
            cur.execute(
                "UPDATE INTO datatype SET logicalname = %s, description = %s, itemtype = %s) WHERE datatypeid = %s",
                (self.logicalName, self.description, self.itemType, self.id)
            )
        else:
            ## create record
            cur.execute(
                "INSERT INTO datatype (logicalname, description, itemtype) VALUES (%s, %s, %s) RETURNING datatypeid",
                (self.logicalName, self.description, self.itemType)
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
            "DELETE FROM datatype WHERE datatypeid = %s",
            (self.id)
        )
        conn.commit()
        cur.close()
