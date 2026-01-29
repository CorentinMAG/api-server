from __future__ import annotations
from flask import request
from api.routes import BaseAPI
from api.services import TriggerService
from dtr_common.schema import TriggerCreate, TriggerUpdate


class TriggerAPI(BaseAPI[TriggerService]):

    def get(self, id: int | None = None):
        if id is None:
            paginated = self.service.paginate(request.args)
            items = [trigger.to_dict() for trigger in paginated.items]
            return {"pagination": paginated.pagination.model_dump(), "items": items}
        trigger = self.service.get_by_id(id)
        return trigger.to_dict()

    def delete(self, id: int):
        self.service.delete(id)
        self.service.commit()

    def put(self, id: int):
        data = request.json
        schema = TriggerUpdate(**data)
        trigger = self.service.update(id, schema)
        self.service.commit()
        return trigger.to_dict()

    def post(self):
        data = request.json
        schema = TriggerCreate(**data)
        trigger = self.service.create(schema)
        self.service.commit()
        return trigger.to_dict()


bp = TriggerAPI.register(
    "triggers",
    url_prefix="triggers",
    rules=[
        {"route": "/", "defaults": {"id": None}, "methods": ["GET", "POST"]},
        {"route": "/<int:id>", "methods": ["GET", "PUT", "DELETE"]},
    ],
)


# @check_offline_mode()
# @bp.route("/configuration/trigger", methods=["GET"])
# def trigger():
#     """
#     Get trigger configuration - all activated periodical transfer policies.

#     Query parameters:
#     - id: str - Trigger identifier
#     - page: int - Page number for pagination (default: 1)
#     - page_size: int - Items per page (default: 10)
#     """
#     trigger_id = request.args.get("id", type=str, default=None)
#     page = request.args.get("page", type=int, default=1)
#     page_size = request.args.get("page_size", type=int, default=10)

#     app = custom_app()

#     trigger = app.services.triggers.get_by_name(trigger_id)

#     return {"configuration": trigger.to_dict(), "pagination": {}, "policies": []}