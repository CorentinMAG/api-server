from .triggers import TriggerService
from .parameters import GlobalParameterService
from api.models import db
from api.repositories import RepositoryFactory
from .worker import WorkerService
from .requests import TransferRequestService

class ServiceContainer:

    def __init__(self) -> None:
        self._repositories = RepositoryFactory(db)
        self._params = GlobalParameterService(self._repositories.parameters)
        self._triggers = TriggerService(
            self._repositories.triggers,
            self._params
        )
        self._workers = WorkerService(self._repositories.workers)
        self._requests = TransferRequestService(self._repositories.requests)

    @property
    def repositories(self) -> RepositoryFactory:
        return self._repositories
    
    @property
    def triggers(self) -> TriggerService:
        return self._triggers
    
    @property
    def params(self) -> GlobalParameterService:
        return self._params
    
    @property
    def workers(self) -> WorkerService:
        return self._workers
    
    @property
    def requests(self) -> TransferRequestService:
        return self._requests