"""
Repository package providing data access abstractions.

This package implements the repository pattern to abstract database operations
and enable dependency injection for better testability.
"""

from __future__ import annotations

from .transfer_request_repository import TransferRequestRepository

__all__ = [
    "BaseRepository",
    "TransferRequestRepository"
]
