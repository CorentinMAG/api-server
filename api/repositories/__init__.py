from .base import BaseRepository
from .parameters import GlobalParametersRepository
from .policy import TransferPolicyRepository
from .queue import QueueRepository
from .request import TransferRequestRepository
from .server import NotificationServerRepository
from .target import TargetRepository
from .trigger import TriggerRepository
from .worker import WorkerRepository

DTR_REPOSITORIES = {cls.__name__: cls for cls in BaseRepository.__subclasses__()}

__all__ = [
    "GlobalParametersRepository",
    "TransferPolicyRepository",
    "QueueRepository",
    "TransferRequestRepository",
    "NotificationServerRepository",
    "TargetRepository",
    "TriggerRepository",
    "WorkerRepository"
]