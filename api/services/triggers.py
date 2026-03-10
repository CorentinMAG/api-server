from .base import BaseService
from api.models import Trigger
from api.repositories import TriggerRepository
from dtr_common.schema import TriggerCreate, TriggerUpdate
from api.services import GlobalParametersService


class TriggerService(BaseService[TriggerRepository]):
    parameters: GlobalParametersService

    def get_by_name(self, name: str | None) -> Trigger:
        if name:
            return self.repository.get_by_name(name)
        else:
            parameters = self.parameters.get()
            return Trigger(polling_interval=parameters.polling_interval, name="default")

    def get_by_id(self, id: int) -> Trigger:
        return self.repository.get_by_id(id)

    def create(self, schema: TriggerCreate) -> Trigger:
        return self.repository.create(schema)

    def update(self, id: int, schema: TriggerUpdate) -> Trigger:
        trigger = self.get_by_id(id)
        return self.repository.update(id, schema.model_dump())

    def delete(self, id: int):
        trigger = self.get_by_id(id)
        self.repository.delete(trigger)