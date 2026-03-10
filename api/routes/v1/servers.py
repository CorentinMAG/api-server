from __future__ import annotations

from flask import request

from api.dtr_common.schema import ServerCreate, ServerUpdate
from api.routes import BaseAPI
from api.services import NotificationServerService
from api.utils import check_offline_mode


class NotificationServerAPI(BaseAPI[NotificationServerService]):

    decorators = [check_offline_mode]

    def get(self, id: int | None = None):
        if id is None:
            paginated = self.service.paginate(request.args)
            items = [server.to_dict() for server in paginated.items]
            print(paginated)

            return {
                "pagination": paginated.pagination.model_dump(),
                "items": items,
            }
        server = self.service.get_by_id(id)
        return server.to_dict()

    def put(self, id: int):
        data = request.json
        schema = ServerUpdate(**data)
        server = self.service.update(id, schema)
        self.service.commit()
        return server.to_dict()

    def delete(self, id: int):
        self.service.delete(id)
        self.service.commit()
        return "", 200

    def post(self):
        data = request.json
        schema = ServerCreate(**data)
        server = self.service.create(schema)
        self.service.commit()
        return server.to_dict()


bp = NotificationServerAPI.register(
    "servers",
    url_prefix="servers",
    rules=[
        {"route": "/", "defaults": {"id": None}, "methods": ["GET", "POST"]},
        {"route": "/<int:id>", "methods": ["GET", "PUT", "DELETE"]},
    ],
)
