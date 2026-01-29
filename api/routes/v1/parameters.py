from __future__ import annotations
from flask import request
from dtr_common.schema import (
    GlobalParametersCreate,
    GlobalParametersUpdate,
)
from api.routes import BaseAPI
from api.services import GlobalParametersService


class GlobalParametersAPI(BaseAPI[GlobalParametersService]):
    def get(self):
        params = self.service.get()
        if params:
            return params.to_dict()
        return "", 404

    def put(self):
        data = request.json
        schema = GlobalParametersUpdate(**data)
        params = self.service.update(schema)
        self.service.commit()
        return params.to_dict()

    def delete(self):
        self.service.delete()
        self.service.commit()
        return "", 200

    def post(self):
        data = request.json
        schema = GlobalParametersCreate(**data)
        params = self.service.create(schema)
        self.service.commit()
        return params.to_dict()


bp = GlobalParametersAPI.register(
    "parameters", url_prefix="parameters", rules=[{"route": "/"}]
)