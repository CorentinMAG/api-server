from __future__ import annotations

from .credentials import Credentials
from .notifications import KafkaParameters, Notification
from .parameters import (
    GlobalParameters,
    TargetParameters,
    TransferPolicyParameters,
)
from .policies import DestinationPolicy, SourcePolicy, TransferPolicy
from .queue import Queue
from .request import TransferRequest
from .server import NotificationServer
from .states import State
from .target import Target
from .trigger import Trigger
from .worker import Worker
from .base import Base

__all__ = [
    "NotificationServer",
    "Queue",
    "Target",
    "Credentials",
    "TransferPolicy",
    "SourcePolicy",
    "DestinationPolicy",
    "GlobalParameters",
    "TransferPolicyParameters",
    "KafkaParameters",
    "TransferRequest",
    "State",
    "TargetParameters",
    "Trigger",
    "Worker",
    "Notification",
]

DTR_MODELS = {
    "NotificationServer": NotificationServer,
    "Trigger": Trigger,
    "Worker": Worker,
    "Target": Target,
    "GlobalParameter": GlobalParameters,
    "TransferPolicy": TransferPolicy,
    "TransferRequest": TransferRequest,
    "Queue": Queue,
}
