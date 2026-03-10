from __future__ import annotations

import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from api.dtr_common.constantes import (
    State as StateEnum,
    SubState as SubStateEnum,
)
from api.exceptions import NotFoundException
from api.models import State, TransferPolicy, TransferRequest

from .base import BaseRepository

SortingOptions = Literal["ASC", "DESC"]


class TransferRequestRepository(BaseRepository[TransferRequest]):
    """repository fro TransferRequest"""

    def get_by_state(self, state: StateEnum, skip: int = 0, limit: int = 100) -> list[TransferRequest]:
        query = (
            select(TransferRequest)
            .join(State, TransferRequest.current_state_id == State.id)
            .where(State.state == state)
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.scalars(query).all())

    def add_state(self, id: int, state: StateEnum) -> None:
        """append a new state to a given request"""
        query = (
            select(TransferRequest)
            .join(State, TransferRequest.current_state_id == State.id)
            .where(TransferRequest.id == id)
            .options(selectinload(TransferRequest.states))
        )
        request = self.session.scalars(query)
        request.states.append(State(state=state))
        self.session.flush()

    def get_by_uid(self, uid: UUID) -> TransferRequest:
        """get transfer request by uid"""
        query = select(TransferRequest).where(TransferRequest.uid == uid)
        obj = self.session.scalar(query)
        if not obj:
            raise NotFoundException(f"TransferRequest with uid {uid} not found")
        return obj

    def get_next_request(
        self,
        state: StateEnum | None = None,
        sub_state: SubStateEnum | None = None,
        queues: list[str] | None = None,
        priority: SortingOptions = "ASC",
        created_at: SortingOptions = "ASC",
        size: int | None = None,
    ) -> TransferRequest | None:
        """get next transfer request based on current state"""

        query = (
            select(TransferRequest)
            .join(TransferRequest.policy)
            .join(TransferPolicy.queue)
            .join(State, TransferRequest.current_state_id == State.id)
        )

        if state:
            query = query.where(State.state == state)
        if sub_state:
            query = query.where(State.sub_state == sub_state)
        if size is not None:
            query = query.where(TransferRequest.size <= size)
        if queues:
            query = query.where(TransferPolicy.queue.in_(queues))

        query = query.order_by(
            (TransferPolicy.priority.asc() if priority == "ASC" else TransferPolicy.priority.desc()),
            (TransferRequest.created_at.asc() if created_at == "ASC" else TransferRequest.created_at.desc()),
        )

        query = query.where(
            or_(
                TransferRequest.next_retry_min_time <= datetime.datetime.now(datetime.timezone.utc),
                TransferRequest.next_retry_min_time.is_(None),
            )
        )
        query = query.with_for_update(skip_locked=True, of=TransferRequest)
        return self.session.scalar(query)
