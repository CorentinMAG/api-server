from __future__ import annotations

from api.dtr_common.constantes import Mode
from api.dtr_common.schema import (
    GlobalParametersCreate,
    GlobalParametersUpdate,
)
from api.models import GlobalParameters
from api.repositories import GlobalParametersRepository

from .base import BaseService


class GlobalParametersService(BaseService[GlobalParametersRepository]):
    def get(self) -> GlobalParameters | None:
        return self.repository.get()

    def delete(self) -> None:
        params = self.get()
        if params:
            self.repository.delete(params)

    def create(self, schema: GlobalParametersCreate) -> GlobalParameters:
        params = GlobalParameters(**schema.model_dump())
        return self.repository.create(params)

    def update(self, schema: GlobalParametersUpdate) -> GlobalParameters:
        return self.repository.update(schema.model_dump(exclude_none=True))

    def switch(self, mode: Mode) -> GlobalParameters | None:
        parameters = self.repository.get()
        if parameters:
            return self.repository.update({"mode": mode})
