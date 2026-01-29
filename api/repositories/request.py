from sqlalchemy.orm import selectinload
from sqlalchemy import select, or_
from .base import BaseRepository
from api.models import TransferRequest, State, TransferPolicy, Queue
import uuid
from api.exception import NotFoundException
from dtr_common.constantes import State as StateEnum, SubState as SubStateEnum
import datetime
from typing import Literal

SortingOptions = Literal["ASC", "DESC"]

class TransferRequestRepository(BaseRepository[TransferRequest]):
    """repository for common TransferRequest operations"""

    def get_by_uuid(self, uuid: uuid.UUID) -> TransferRequest:
        query = (
            select(TransferRequest)
            .where(TransferRequest.uid == uuid)
        )
        obj = self.session.scalar(query)
        if not obj:
            raise NotFoundException(f"TransferRequest with uuid {uuid} not found")
        return obj
    
    def get_by_state(self, state: StateEnum, skip: int = 0, limit: int = 100) -> list[TransferRequest]:
        query = (
            select(TransferRequest)
            .join(State, TransferRequest.current_state_id == State.id)
            .where(State.state == state)
            .offset(skip)
            .limit(limit)
        ) 
        return list(self.session.scalars(query).unique().all())
    
    def get_with_relations(self, skip: int = 0, limit: int = 100, filters: dict[str, any] | None = None):
        pass
    
    def add_state(self, id: int, state: StateEnum) -> None:
        """append a new state to a given transfer request"""
        query = (
            select(TransferRequest)
            .join(State, TransferRequest.current_state_id == State.id)
            .where(TransferRequest.id == id)
            .options(selectinload(TransferRequest.states))
        )
        request = self.session.scalar(query)
        request.states.append(State(state))
        self.session.flush()
    
    def get_next_request(
            self, 
            size: int | None = None,
            state: StateEnum | None = None,
            sub_state: SubStateEnum | None = None,
            queues: list[str] | None = None,
            priority: SortingOptions = "ASC",
            created_at: SortingOptions = "ASC",
            ):
        """get next transfer request"""

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
            query = query.where(
                or_(
                    TransferRequest.size < size,
                    TransferRequest.size.is_(None)
                )
            )
        if queues:
            query = query.where(Queue.name.in_(queues))

        query = query.order_by(
            (
                Queue.priority.asc()
                if priority == "ASC"
                else Queue.priority.desc()
            ),
            (
                TransferRequest.created_at.asc()
                if created_at == "ASC"
                else TransferRequest.created_at.desc()
            )
        )

        now = datetime.datetime.now(datetime.timezone.utc)

        query = query.where(
            or_(
                TransferRequest.next_retry_min_time <= now,
                TransferRequest.next_retry_min_time.is_(None)
            )
        )
        query = query.with_for_update(of=TransferRequest, skip_locked=True)
        return self.session.scalar(query)
