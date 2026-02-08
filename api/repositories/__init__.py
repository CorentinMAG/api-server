from .base import BaseRepository
from .parameters import GlobalParametersRepository
from .queue import QueueRepository
from .server import NotificationServerRepository
from .target import TargetRepository
from .trigger import TriggerRepository
from .worker import WorkerRepository


DTR_REPOSITORIES = {cls.__name__: cls for cls in BaseRepository.__subclasses__()}
