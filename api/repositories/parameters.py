from api.models import GlobalParameters
from .base import BaseRepository
from api.exception import NotConfiguredException


class GlobalParametersRepository(BaseRepository[GlobalParameters]):

    def get(self) -> GlobalParameters | None:
        query = self.base_query().limit(1)
        return self.session.scalar(query)

    def update(self, data: dict[str, any]) -> GlobalParameters:
        params = self.get()
        if params:
            updated_params = super().update(params, data)
            return updated_params
        raise NotConfiguredException("Global parameters not configured yet")

    def create(self, parameters: GlobalParameters) -> GlobalParameters:
        """
        we only have 1 globalParameters.
        We delete existing one
        """
        params = self.get()
        if params:
            self.session.delete(params)
        self.session.add(parameters)
        self.session.flush()
        return parameters

    def delete(self) -> None:
        params = self.get()
        if params:
            self.session.delete(params)
            self.session.flush()
