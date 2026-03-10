from __future__ import annotations

from api.dtr_common.schema import WorkerCreate, WorkerUpdate
from api.models import Worker
from api.repositories import WorkerRepository
from api.services import QueueService

from .base import BaseService


class WorkerService(BaseService[WorkerRepository]):
    queue: QueueService

    def get_by_name(self, name: str) -> Worker:
        return self.repository.get_by_name(name)

    def get_by_id(self, id: int) -> Worker:
        return self.repository.get_by_id(id)

    def create(self, schema: WorkerCreate) -> Worker:
        worker = Worker(name=schema.name)
        self.repository.create(worker)

    def update(self, id: int, schema: WorkerUpdate) -> Worker:
        worker = self.get_by_id(id)
        self.repository.update(worker, schema.to_dict())

    def delete(self, id: int):
        worker = self.get_by_id(id)
        self.repository.delete(worker)
