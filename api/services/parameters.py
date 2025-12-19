from .base import BaseService
from ..repositories import GlobalParametersRepository
from ..models import GlobalParameters
from dtr_common.constantes import Mode

class GlobalParameterService(BaseService[GlobalParametersRepository]):

    def __init__(self, repository: GlobalParametersRepository) -> None:
        super().__init__(repository)


    def get(self) -> GlobalParameters | None:
        return self.repository.get_params()

    def switch_mode(self, mode: Mode) -> None:
        params = self.repository.get_params()
        self.repository.update(params, {"mode": mode})
        self.repository.session.commit()