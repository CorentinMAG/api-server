from .parameters import GlobalParameterService
from .targets import TargetService
from .policy import TransferPolicyService
from .trigger import TriggerService
from .worker import WorkerService
from .queue import QueueService
from .servers import NotificationServerService


DTR_SERVICES = {
    "GlobalParameterService": GlobalParameterService,
    "TargetService": TargetService,
    "TransferPolicyService": TransferPolicyService,
    "TriggerService": TriggerService,
    "WorkerService": WorkerService,
    "TriggerService": TriggerService,
    "QueueService": QueueService,
    "NotificationServerService": NotificationServerService,
}
