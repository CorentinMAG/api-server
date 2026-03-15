from api.models import Worker
from .base import BaseService
from api.repositories import WorkerRepository
from dtr_common.schema import WorkerCreate, WorkerUpdate
from api.models import Worker
from api.services import QueueService
from werkzeug.datastructures import ImmutableMultiDict
from dtr_common.schema import Pagination


class WorkerService(BaseService[WorkerRepository]):

    queue: QueueService

    def get_by_name(self, name: str) -> Worker:
        return self.repository.get_by_name(name)

    def get_by_id(self, id: int) -> Worker:
        return self.repository.get_by_id(id)

    def paginate(self, args: ImmutableMultiDict) -> Pagination[Worker]:
        return self.repository.paginate(args)

    def create(self, schema: WorkerCreate) -> Worker:
        queues = [self.queue.get_by_name(name) for name in schema.queues]
        worker = Worker(name=schema.name, queues=queues)
        return self.repository.create(worker)

    def update(self, id: int, schema: WorkerUpdate) -> Worker:
        worker = self.get_by_id(id)
        if schema.queues is not None:
            worker.queues = [self.queue.get_by_name(name) for name in schema.queues]
        return self.repository.update(
            worker, schema.model_dump(exclude_none=True, exclude={"queues"})
        )

    def delete(self, id: int):
        worker = self.get_by_id(id)
        self.repository.delete(worker)
