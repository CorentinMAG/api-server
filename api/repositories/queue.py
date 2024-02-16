from ..models import Queue
from .base import BaseRepository
from flask_sqlalchemy import SQLAlchemy
from ..db import db

class QueueRepository(BaseRepository):

    def __init__(self, db: SQLAlchemy) -> None:
        self.db = db

    def get_by_id(self, id: int) -> Queue:
        return self.db.session.query(Queue).get(id)
    
    def get_all(self) -> list[Queue]:
        return self.db.session.query(Queue).all()

    def add(self, queue: Queue) -> int:
        self.db.session.add(queue)
        self.db.session.commit()
        return queue

    def remove(self, queue: Queue) -> None:
        self.db.session.delete(queue)
        self.db.session.commit()
    
    def flush(self) -> None:
        self.db.session.query(Queue).delete()
        self.db.session.commit()

repository = QueueRepository(db)