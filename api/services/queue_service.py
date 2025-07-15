"""
Queue Service for transfer request queue management.

This service handles queue capacity checking, limits, and optimization
logic as part of the service layer decomposition.
"""

from __future__ import annotations

from typing import NamedTuple

from api.models import Queue
from api.repositories import TransferRequestRepository


class QueueCapacityInfo(NamedTuple):
    """Information about queue capacity and availability."""

    available_slots: int
    queued_count: int
    max_files_per_destination: int
    is_full: bool
    is_near_threshold: bool


class QueueService:
    """Service for managing transfer request queues."""

    def __init__(self, transfer_request_repo: TransferRequestRepository, logger=None):
        """
        Initialize queue service with dependencies.

        Args:
            transfer_request_repo: Repository for transfer request operations
            logger: Logger instance for queue operations
        """
        self.transfer_request_repo = transfer_request_repo
        self.logger = logger

    def check_queue_capacity(
        self, policy_id: int, queue: Queue, num_destinations: int, num_triggered_files: int
    ) -> QueueCapacityInfo:
        """
        Check queue capacity and calculate available slots.

        Args:
            policy_id: Transfer policy ID
            queue: Queue configuration
            num_destinations: Number of destination policies
            num_triggered_files: Number of files to potentially queue

        Returns:
            QueueCapacityInfo with capacity details
        """
        # Count currently queued requests for this policy
        queued_count = self.transfer_request_repo.count_queued_requests_for_policy(policy_id)

        # Calculate available slots
        available_slots = queue.queue_limit - queued_count

        # Check if queue is full (need space for at least one file per destination)
        is_full = available_slots <= num_destinations

        # Calculate max files we can process
        max_files_per_destination = 0 if is_full else available_slots // num_destinations

        # Check if near threshold
        is_near_threshold = queued_count + num_triggered_files >= queue.queue_threshold

        return QueueCapacityInfo(
            available_slots=available_slots,
            queued_count=queued_count,
            max_files_per_destination=max_files_per_destination,
            is_full=is_full,
            is_near_threshold=is_near_threshold,
        )

    def log_queue_warning_if_needed(self, capacity_info: QueueCapacityInfo, queue: Queue) -> None:
        """Log warning if queue is approaching capacity limits."""
        if capacity_info.is_near_threshold and self.logger:
            self.logger.warning(
                "queue %s is almost full (%d/%d)",
                queue.name,
                capacity_info.queued_count,
                queue.queue_limit,
            )

    def can_accept_files(self, policy_id: int, queue: Queue, num_destinations: int, num_files: int) -> bool:
        """
        Check if queue can accept the specified number of files.

        Args:
            policy_id: Transfer policy ID
            queue: Queue configuration
            num_destinations: Number of destination policies
            num_files: Number of files to queue

        Returns:
            True if queue can accept the files, False otherwise
        """
        capacity_info = self.check_queue_capacity(policy_id, queue, num_destinations, num_files)
        return not capacity_info.is_full and capacity_info.max_files_per_destination >= num_files

    def get_max_processable_files(self, policy_id: int, queue: Queue, num_destinations: int) -> int:
        """
        Get the maximum number of files that can be processed given current queue state.

        Args:
            policy_id: Transfer policy ID
            queue: Queue configuration
            num_destinations: Number of destination policies

        Returns:
            Maximum number of files that can be queued
        """
        capacity_info = self.check_queue_capacity(policy_id, queue, num_destinations, 0)
        return capacity_info.max_files_per_destination
