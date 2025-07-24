"""
Queue repository providing specialized database operations.

This repository implements queue-specific queries and management operations.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.models import Queue, TransferPolicy

from .base import BaseRepository


class QueueRepository(BaseRepository[Queue]):
    """Repository for Queue operations with specialized queries."""

    def __init__(self, db_session: Session):
        super().__init__(Queue, db_session)

    def find_by_criteria(self, **criteria) -> List[Queue]:
        """Find queues by basic criteria."""
        query = select(self.model_class)
        for key, value in criteria.items():
            if hasattr(self.model_class, key):
                query = query.where(getattr(self.model_class, key) == value)
        return list(self.db_session.execute(query).scalars().all())

    def find_by_name(self, name: str) -> Optional[Queue]:
        """Find queue by name."""
        stmt = select(Queue).where(Queue.name == name)
        return self.db_session.scalar(stmt)

    def find_all_ordered_by_priority(self) -> List[Queue]:
        """Find all queues ordered by priority."""
        stmt = select(Queue).order_by(Queue.priority.asc())
        return list(self.db_session.execute(stmt).scalars().all())

    def find_high_priority_queues(self, max_priority: int = 5) -> List[Queue]:
        """Find queues with high priority (low priority values)."""
        stmt = select(Queue).where(Queue.priority <= max_priority).order_by(Queue.priority.asc())
        return list(self.db_session.execute(stmt).scalars().all())

    def get_queue_statistics(self, queue_id: int) -> dict:
        """Get statistics for a queue."""
        queue = self.get_by_id(queue_id)
        if not queue:
            return {}

        # Count policies using this queue
        policy_count_stmt = select(func.count(TransferPolicy.id)).where(TransferPolicy.queue_id == queue_id)
        policy_count = self.db_session.execute(policy_count_stmt).scalar() or 0

        return {
            "queue_id": queue_id,
            "name": queue.name,
            "priority": queue.priority,
            "queue_limit": queue.queue_limit,
            "queue_threshold": queue.queue_threshold,
            "queue_timeout": queue.queue_timeout,
            "policies_using_queue": policy_count,
        }

    def find_queues_by_capacity_range(
        self, min_limit: Optional[int] = None, max_limit: Optional[int] = None
    ) -> List[Queue]:
        """Find queues within a capacity range."""
        stmt = select(Queue)

        if min_limit is not None:
            stmt = stmt.where(Queue.queue_limit >= min_limit)
        if max_limit is not None:
            stmt = stmt.where(Queue.queue_limit <= max_limit)

        stmt = stmt.order_by(Queue.queue_limit.asc())
        return list(self.db_session.execute(stmt).scalars().all())

    def get_queue_with_policies(self, queue_id: int) -> Optional[Queue]:
        """Get queue with all associated policies loaded."""
        # Since Queue doesn't have a policies relationship defined,
        # we load the queue and separately query policies
        queue = self.get_by_id(queue_id)
        if queue:
            # Load associated policies separately
            policies_stmt = select(TransferPolicy).where(TransferPolicy.queue_id == queue_id)
            policies = list(self.db_session.execute(policies_stmt).scalars().all())
            # Attach policies as a dynamic attribute for compatibility
            queue._policies = policies
        return queue

    def find_unused_queues(self) -> List[Queue]:
        """Find queues that are not being used by any policies."""
        stmt = select(Queue).outerjoin(TransferPolicy).where(TransferPolicy.id.is_(None))
        return list(self.db_session.execute(stmt).scalars().all())

    def update_queue_limits(self, queue_id: int, new_limit: int, new_threshold: int) -> bool:
        """Update queue limits and threshold."""
        queue = self.get_by_id(queue_id)
        if not queue:
            return False

        try:
            queue.queue_limit = new_limit
            queue.queue_threshold = new_threshold
            return True
        except Exception:
            return False
