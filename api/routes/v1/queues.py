from flask import request
from dtr_common.schema import QueueCreate, QueueUpdate
from api.routes import BaseAPI
from api.services import QueueService
from api.utils import check_offline_mode


class QueueAPI(BaseAPI[QueueService]):

    decorators = [check_offline_mode()]

    prefix = "queues"

    def get(self, id: int | None = None):
        if id is None:
            paginated = self.service.paginate(request.args)
            items = [queue.to_dict() for queue in paginated.items]
            return {
                "pagination": paginated.pagination.model_dump(),
                "items": items,
            }
        queue = self.service.get_by_id(id)
        return queue.to_dict()

    def delete(self, id: int):
        self.service.delete(id)
        self.service.commit()
        return "", 200

    def put(self, id: int):
        data = request.json
        schema = QueueUpdate(**data)
        queue = self.service.update(id, schema)
        self.service.commit()
        return queue.to_dict()

    def post(self):
        data = request.json
        schema = QueueCreate(**data)
        queue = self.service.create(schema)
        self.service.commit()
        return queue.to_dict()
