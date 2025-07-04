"""
TransferRequest repository providing specialized database operations.

This repository implements complex queries specific to transfer request
management, including queue operations and state filtering.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Set

from dtr_common.constantes import State as StateEnum, SubState as SubStateEnum
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from api.models import Queue, State, TransferPolicy, TransferRequest

from .base import BaseRepository


class TransferRequestRepository(BaseRepository[TransferRequest]):
    """Repository for TransferRequest operations with complex queries."""

    def __init__(self, db_session: Session):
        super().__init__(TransferRequest, db_session)

    def find_by_criteria(self, **criteria) -> List[TransferRequest]:
        """Find transfer requests by basic criteria."""
        query = select(self.model_class)
        for key, value in criteria.items():
            if hasattr(self.model_class, key):
                query = query.where(getattr(self.model_class, key) == value)
        return list(self.db_session.execute(query).scalars().all())

    def get_next_available_request(
        self,
        state: Optional[StateEnum] = None,
        sub_state: Optional[SubStateEnum] = None,
        max_size: Optional[int] = None,
    ) -> Optional[TransferRequest]:
        """
        Get the next available transfer request based on queue priority.

        Args:
            state: Filter by current state
            sub_state: Filter by current sub-state
            max_size: Maximum file size limit

        Returns:
            Next available transfer request or None
        """
        base = (
            select(TransferRequest)
            .join(TransferPolicy)
            .join(Queue)
            .order_by(Queue.priority.asc(), TransferRequest.created_at.asc())
        )

        if state or sub_state:
            # Use window function to find latest state for each request
            latest_state_cte = select(
                State.id.label("state_id"),
                State.request_id,
                State.state,
                State.sub_state,
                func.row_number().over(partition_by=State.request_id, order_by=State.id.desc()).label("rn"),
            ).cte("latest_state")

            base = base.join(
                latest_state_cte,
                latest_state_cte.c.request_id == TransferRequest.id,
            ).where(latest_state_cte.c.rn == 1)

            if sub_state:
                base = base.where(latest_state_cte.c.sub_state == sub_state)
            else:
                base = base.where(latest_state_cte.c.state == state)

        if max_size:
            now = datetime.now(timezone.utc)
            base = base.where(
                or_(TransferRequest.size < max_size, TransferRequest.size.is_(None)),
                or_(
                    TransferRequest.next_retry_min_time.is_(None), TransferRequest.next_retry_min_time <= now
                ),
            )

        base = base.with_for_update(skip_locked=True).limit(1)
        return self.db_session.scalar(base)

    def count_queued_requests_for_policy(self, policy_id: int) -> int:
        """Count transfer requests in QUEUED state for a specific policy."""
        latest_state_subquery = (
            select(func.max(State.id))
            .group_by(State.request_id)
            .where(State.request_id == TransferRequest.id)
            .correlate(TransferRequest)
            .scalar_subquery()
        )

        queued_count_stmt = (
            select(func.count(TransferRequest.id))
            .join(State, TransferRequest.id == State.request_id)
            .where(
                TransferRequest.policy_id == policy_id,
                State.id == latest_state_subquery,
                State.state == StateEnum.QUEUED,
            )
        )
        return self.db_session.execute(queued_count_stmt).scalar_one_or_none() or 0

    def get_existing_filenames_for_policy(self, policy_id: int, filenames: Set[str]) -> Set[str]:
        """Get existing filenames for a policy from a set of candidate filenames."""
        if not filenames:
            return set()

        existing_files_stmt = select(TransferRequest.filename).where(
            TransferRequest.policy_id == policy_id,
            TransferRequest.filename.in_(filenames),
        )
        return set(self.db_session.execute(existing_files_stmt).scalars().all())

    def count_unfinished_requests_for_file(self, policy_id: int, filename: str) -> int:
        """Count unfinished transfer requests for a specific file and policy."""
        latest_state_subquery = (
            select(func.max(State.id))
            .group_by(State.request_id)
            .where(State.request_id == TransferRequest.id)
            .correlate(TransferRequest)
            .scalar_subquery()
        )

        unfinished_count_stmt = (
            select(func.count(TransferRequest.id))
            .join(State, TransferRequest.id == State.request_id)
            .where(
                TransferRequest.policy_id == policy_id,
                TransferRequest.filename == filename,
                State.id == latest_state_subquery,
                State.state.not_in([StateEnum.SUCCESSFUL, StateEnum.CANCELLED]),
            )
        )
        return self.db_session.execute(unfinished_count_stmt).scalar_one()

    def find_associated_requests(
        self, filename: str, policy_id: int, exclude_id: int
    ) -> List[TransferRequest]:
        """Find all transfer requests for the same filename and policy, excluding one ID."""
        query = (
            select(TransferRequest)
            .options(joinedload(TransferRequest.states))
            .where(
                TransferRequest.filename == filename,
                TransferRequest.policy_id == policy_id,
                TransferRequest.id != exclude_id,
            )
        )
        return list(self.db_session.execute(query).scalars().unique().all())

    def get_with_lock(self, request_id: int) -> Optional[TransferRequest]:
        """Get transfer request with row-level lock for updates."""
        return self.db_session.query(TransferRequest).with_for_update().get(request_id)

    def find_in_progress_for_destination(
        self, policy_name: str, filename: str, dest_id: int
    ) -> Optional[TransferRequest]:
        """Find existing transfer in progress for specific destination."""
        return self.db_session.scalar(
            select(TransferRequest)
            .join(TransferPolicy)
            .where(TransferPolicy.name == policy_name)
            .where(TransferRequest.filename == filename)
            .where(TransferRequest.dest_id == dest_id)
            .where(
                TransferRequest.states.any(State.state.not_in([StateEnum.SUCCESSFUL, StateEnum.CANCELLED]))
            )
        )

    def filter_by_uid(self, uid) -> Optional[TransferRequest]:
        """Find a transfer request by its UID."""
        stmt = select(TransferRequest).where(TransferRequest.uid == uid)
        return self.db_session.scalar(stmt)
