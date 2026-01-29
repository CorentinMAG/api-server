from .base import BaseService
from .parameters import GlobalParametersService
from .policies import TransferPolicyService
from .requests import TransferRequestService
from .queue import QueueService
from .triggers import TriggerService
from .worker import WorkerService
from .targets import TargetService
from .server import NotificationServerService

DTR_SERVICES = {cls.__name__: cls for cls in BaseService.__subclasses__()}