from ..models import Trigger, TransferPolicy
from sqlalchemy import select
from .base import BaseService
from ..repositories import TriggerRepository
from .parameters import GlobalParameterService
from dtr_common.constantes import Type

class TriggerService(BaseService[TriggerRepository]):

    def __init__(self, repository: TriggerRepository, parameters: GlobalParameterService) -> None:
        super().__init__(repository)
        self._parameters = parameters

    def get_by_name(self, name: str) -> Trigger:
        if name == "default":
            gparams = self._parameters.get()
            return Trigger(name = "default", polling_interval = gparams.polling_interval)
        return self.repository.get_by_name(name)

    def get_policies(self, name: str, page: int = 1, page_size: int = 100):
        query = (
            select(TransferPolicy)
            .outerjoin(Trigger)
            .where(
                TransferPolicy.enabled == True,
                TransferPolicy.type == Type.PERIODICAL
            )
        )
        if name == "default":
            query = query.where(TransferPolicy.trigger_id.is_(None))
        else:
            query = query.where(Trigger.name == name)
        return self.repository.get_policies(query, page, page_size)