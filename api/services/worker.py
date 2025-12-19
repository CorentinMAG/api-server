from .base import BaseService
from ..repositories import WorkerRepository
from api.models import Worker

class WorkerService(BaseService[WorkerRepository]):
    def __init__(self, repository: WorkerRepository) -> None:
        super().__init__(repository)


    def get_by_name(self, name: str) -> Worker | None:
        if name != "default":
            return self.repository.get_by_name(name)
        return