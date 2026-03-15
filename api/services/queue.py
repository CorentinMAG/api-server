from .base import BaseService
from api.repositories import QueueRepository
from api.models import Queue
from dtr_common.schema import QueueCreate, QueueUpdate, Pagination
from werkzeug.datastructures import ImmutableMultiDict


class QueueService(BaseService[QueueRepository]):

    def get_by_name(self, name: str) -> Queue:
        return self.repository.get_by_name(name)

    def get_by_id(self, id: int) -> Queue:
        return self.repository.get_by_id(id)

    def paginate(self, args: ImmutableMultiDict) -> Pagination[Queue]:
        return self.repository.paginate(args)

    def create(self, schema: QueueCreate) -> Queue:
        queue = Queue(**schema.model_dump())
        return self.repository.create(queue)

    def delete(self, id: int):
        queue = self.repository.get_by_id(id)
        return self.repository.delete(queue)

    def update(self, id: int, schema: QueueUpdate) -> Queue:
        queue = self.repository.get_by_id(id)
        return self.repository.update(queue, schema.model_dump(exclude_none=True))
