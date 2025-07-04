"""
Repository package providing data access abstractions.

This package implements the repository pattern to abstract database operations
and enable dependency injection for better testability.
"""
from __future__ import annotations

from .base import BaseRepository, TransactionalRepository
from .queue_repository import QueueRepository
from .target_repository import TargetRepository
from .transfer_policy_repository import TransferPolicyRepository
from .transfer_request_repository import TransferRequestRepository

__all__ = [
    "BaseRepository",
    "TransactionalRepository",
    "TransferRequestRepository",
    "TransferPolicyRepository",
    "QueueRepository",
    "TargetRepository",
]
