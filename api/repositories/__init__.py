from .parameters import GlobalParametersRepository
from .policy import TransferPolicyRepository
from .queue import QueueRepository
from .target import TargetRepository
from .server import NotificationServerRepository
from .trigger import TriggerRepository
from .worker import WorkerRepository
from .request import TransferRequestRepository
from flask_sqlalchemy import SQLAlchemy

class RepositoryFactory:
    """factory for creating repositories"""

    def __init__(self, db: SQLAlchemy) -> None:
        self._db = db
        self._targets = TargetRepository(db)
        self._servers = NotificationServerRepository(db)
        self._policies = TransferPolicyRepository(db)
        self._queues = QueueRepository(db)
        self._workers = WorkerRepository(db)
        self._parameters = GlobalParametersRepository(db)
        self._triggers = TriggerRepository(db)
        self._requests = TransferRequestRepository(db)

    @property
    def targets(self) -> TargetRepository:
        return self._targets
    
    @property
    def servers(self) -> NotificationServerRepository:
        return self._servers
    
    @property
    def policies(self) -> TransferPolicyRepository:
        return self._policies
    
    @property
    def queues(self) -> QueueRepository:
        return self._queues
    
    @property
    def workers(self) -> WorkerRepository:
        return self._workers
    
    @property
    def parameters(self) -> GlobalParametersRepository:
        return self._parameters
    
    @property
    def triggers(self) -> TriggerRepository:
        return self._triggers
    
    @property
    def requests(self) -> TransferRequestRepository:
        return self._requests