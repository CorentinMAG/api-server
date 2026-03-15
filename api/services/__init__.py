from .base import BaseService
from .targets import TargetService
from .queue import QueueService
from .server import NotificationServerService
from .parameters import GlobalParametersService
from .triggers import TriggerService
from .policies import TransferPolicyService
from .worker import WorkerService
from .requests import TransferRequestService

DTR_SERVICES = {cls.__name__: cls for cls in BaseService.__subclasses__()}