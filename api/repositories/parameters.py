from sqlalchemy import select
from api.models import GlobalParameters
from .base import BaseRepository


class GlobalParametersRepository(BaseRepository[GlobalParameters]):

    def get(self) -> GlobalParameters | None:
        query = select(GlobalParameters).limit(1)
        return self.session.execute(query).scalar()

    def update(self, data: dict[str, any]) -> GlobalParameters:
        params = self.get()
        if params:
            updated_params = super().update(params, data)
            return updated_params

    def get_with_relations(
        self, skip: int = 0, limit: int = 100, filters: dict[str, any] | None = None
    ) -> list[GlobalParameters]:
        params = self.get()
        return [params] if params else []

    def create(self, parameters: GlobalParameters) -> GlobalParameters:
        """
        We have only 1 globalparameters
        """
        params = self.get()
        if params:
            self.session.delete(params)
        self.session.add(parameters)
        self.session.flush()
        return parameters
