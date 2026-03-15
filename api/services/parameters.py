from .base import BaseService
from api.repositories import GlobalParametersRepository
from api.models import GlobalParameters
from dtr_common.constantes import Mode
from dtr_common.schema import (
    GlobalParametersCreate,
    GlobalParametersUpdate,
)
from werkzeug.datastructures import ImmutableMultiDict
from dtr_common.schema import Pagination


class GlobalParametersService(BaseService[GlobalParametersRepository]):

    def get(self) -> GlobalParameters | None:
        return self.repository.get()

    def delete(self) -> None:
        self.repository.delete()

    def create(self, schema: GlobalParametersCreate) -> GlobalParameters:
        params = GlobalParameters(**schema.model_dump())
        return self.repository.create(params)

    def update(self, schema: GlobalParametersUpdate) -> GlobalParameters:
        return self.repository.update(schema.model_dump(exclude_none=True))

    def switch(self, mode: Mode) -> GlobalParameters | None:
        return self.repository.update({"mode": mode})

    def get_by_id(self, id: int) -> GlobalParameters:
        return self.repository.get_by_id(id)

    def get_by_name(self, name: str) -> GlobalParameters:
        return self.repository.get_by_name(name)

    def paginate(self, args: ImmutableMultiDict) -> Pagination[GlobalParameters]:
        return self.repository.paginate(args, eager=None)
