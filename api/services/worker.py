from api.models import Worker
from .base import BaseService
from api.repositories import WorkerRepository
from dtr_common.schema import WorkerCreate, WorkerUpdate
from api.models import Worker


class WorkerService(BaseService[WorkerRepository]):

    def __init__(self):
        super().__init__()
        self.queue_repository = self._get_or_create_repository("QueueRepository")

    def get_by_name(self, name: str) -> Worker:
        return self.repository.get_by_name(name)

    def get_by_id(self, id: int) -> Worker:
        return self.repository.get_by_id(id)

    def create(self, schema: WorkerCreate) -> Worker:
        worker = Worker(name=schema.name)

    def update(self, id: int, schema: WorkerUpdate) -> Worker:
        worker = self.get_by_id(id)
        self.repository.update(worker, schema.to_dict())

    def delete(self, id: int):
        worker = self.get_by_id(id)
        self.repository.delete(worker)