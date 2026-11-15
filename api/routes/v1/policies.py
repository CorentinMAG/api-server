from __future__ import annotations

from flask import request

from api.dtr_common.schema import TransferPolicyCreate, TransferPolicyUpdate
from api.routes import BaseAPI
from api.services import TransferPolicyService
from api.utils import check_offline_mode


class TransferPolicyAPI(BaseAPI[TransferPolicyService]):

    decorators = [check_offline_mode]
    prefix = "policies"

    def get(self, id: int | None = None):
        if id is None:
            paginated = self.service.paginate(request.args)
            items = [policy.to_dict() for policy in paginated.items]
            return {
                "pagination": paginated.pagination.model_dump(),
                "items": items,
            }
        policy = self.service.get_with_relations(id)
        return policy.to_dict()

    def post(self):
        data = request.json
        schema = TransferPolicyCreate(**data)
        policy = self.service.create(schema)
        self.service.commit()
        return policy.to_dict()

    def put(self, id: int):
        data = request.json
        schema = TransferPolicyUpdate(**data)
        policy = self.service.update(id, schema)
        self.service.commit()
        return policy.to_dict()

    def delete(self, id: int):
        self.service.delete(id)
        self.service.commit()
        return "", 200
