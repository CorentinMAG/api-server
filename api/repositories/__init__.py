from .target import TargetRepository
from .policy import TransferPolicyRepository
from .request import TransferRequestRepository
from .parameters import GlobalParameterRepository
from .trigger import TriggerRepository
from .worker import WorkerRepository
from .server import NotificationServerRepository
from .queue import QueueRepository
from .base import BaseRepository


DTR_REPOSITORIES = {
    "TargetRepository": TargetRepository,
    "TransferPolicyRepository": TransferPolicyRepository,
    "TransferRequestRepository": TransferRequestRepository,
    "GlobalParameterRepository": GlobalParameterRepository,
    "TriggerRepository": TriggerRepository,
    "WorkerRepository": WorkerRepository,
    "NotificationServerRepository": NotificationServerRepository,
    "QueueRepository": QueueRepository,
}
