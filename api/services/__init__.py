from __future__ import annotations

from .base import BaseService
from .parameters import GlobalParametersService
from .queue import QueueService
from .servers import NotificationServerService
from .targets import TargetService
from .policy import TransferPolicyService

DTR_SERVICES = {cls.__name__: cls for cls in BaseService.__subclasses__()}
