from flask_sqlalchemy import SQLAlchemy
from .base import BaseRepository
from ..models import Worker
from ..errors import NotFoundError
from sqlalchemy import select
from sqlalchemy.orm import selectinload

class WorkerRepository(BaseRepository[Worker]):
    def __init__(self, db: SQLAlchemy):
        super().__init__(Worker, db)

    def get_by_name(self, name: str) -> Worker:
        query = (
            select(Worker)
            .where(Worker.name == name)
            .options(
                selectinload(Worker.queues)
            )
        )
        obj = self.session.scalar(query)
        if not obj:
            raise NotFoundError(f"Worker with name {name} not found")
        return obj