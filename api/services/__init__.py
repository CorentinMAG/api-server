from .base import BaseService
from .targets import TargetService
from .policy import TransferPolicyService
from .queue import QueueService
from .parameters import GlobalParametersService
from .servers import NotificationServerService

DTR_SERVICES = {cls.__name__: cls for cls in BaseService.__subclasses__()}
