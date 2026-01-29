from __future__ import annotations

from .credentials import Credentials
from .notifications import Notification, NotificationParameter, KafkaParameters
from .parameters import (
    GlobalParameters,
    TargetParameters,
    TransferPolicyParameters
)
from .policies import SourcePolicy, DestinationPolicy, TransferPolicy
from .queue import Queue
from .request import TransferRequest
from .server import NotificationServer
from .states import State
from .target import Target
from .trigger import Trigger
from .worker import Worker

DTR_MODELS = {
    "NotificationServer": NotificationServer,
    "Trigger": Trigger,
    "Worker": Worker,
    "Target": Target,
    "GlobalParameters": GlobalParameters,
    "TransferPolicy": TransferPolicy,
    "TransferRequest": TransferRequest,
    "Queue": Queue
}