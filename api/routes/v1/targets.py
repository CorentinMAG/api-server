from __future__ import annotations

from flask import request

from api.dtr_common.schema import TargetCreate, TargetUpdate
from api.routes import BaseAPI
from api.services import TargetService
from api.utils import check_offline_mode


class TargetAPI(BaseAPI[TargetService]):

    decorators = [check_offline_mode]
    prefix = "targets"

    custom_routes = {"get_info": ("/info", ["GET"])}

    def get_info(self):
        return {"hello": "world"}

    def delete(self, id: int):
        self.service.delete(id)
        self.service.commit()
        return "", 200

    def get(self, id: int | None = None):
        if id is None:
            # return paginated records
            paginated = self.service.paginate(request.args)
            items = [target.to_dict() for target in paginated.items]

            return {
                "pagination": paginated.pagination.model_dump(),
                "items": items,
            }
        target = self.service.get_by_id(id)
        return target.to_dict()

    def post(self):
        data = request.json
        schema = TargetCreate(**data)
        target = self.service.create(schema)
        self.service.commit()
        return target.to_dict()

    def put(self, id: int):
        data = request.json
        schema = TargetUpdate(**data)
        target = self.service.update(id, schema)
        self.service.commit()
        return target.to_dict()
