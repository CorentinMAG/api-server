from .base import BaseService
from .targets import TargetService
from .queue import QueueService
from .server import NotificationServerService
from .parameters import GlobalParametersService
from .policies import TransferPolicyService
from .requests import TransferRequestService
from .triggers import TriggerService
from .worker import WorkerService

DTR_SERVICES = {cls.__name__: cls for cls in BaseService.__subclasses__()}