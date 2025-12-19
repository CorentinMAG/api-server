from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select, or_
from .base import BaseRepository
from ..models import TransferRequest, State, TransferPolicy, Queue, DestinationPolicy, Worker
import uuid
from flask_sqlalchemy import SQLAlchemy
from ..errors import NotFoundError
from dtr_common.constantes import State as StateEnum, SubState as SubStateEnum
import datetime

class TransferRequestRepository(BaseRepository[TransferRequest]):
    def __init__(self, db: SQLAlchemy):
        super().__init__(TransferRequest, db)

    def get_by_uuid(self, uuid: uuid.UUID) -> TransferRequest:
        query = (
            select(TransferRequest)
            .where(TransferRequest.uid == uuid)
            .options(
                joinedload(TransferRequest.states),
                joinedload(TransferRequest.policy),
                joinedload(TransferRequest.dest),
                joinedload(TransferRequest.current_state)
            )
        )
        obj = self.session.scalar(query)
        if not obj:
            raise NotFoundError(f"TransferRequest with uuid {uuid} not found")
        return obj
    
    def get_next_request(
            self, 
            size: int | None = None,
            state: StateEnum | None = None,
            sub_state: SubStateEnum | None = None,
            queues: list[str] | None = None
            ):
        """get next transfer request"""
        now = datetime.datetime.now(datetime.timezone.utc)
        query = (
            select(TransferRequest)
            .join(TransferPolicy)
            .join(Queue)
            .join(State, TransferRequest.current_state_id == State.id)
            .order_by(Queue.priority.asc(), TransferRequest.created_at.asc())
            .options(
                joinedload(TransferRequest.policy),
                joinedload(TransferRequest.dest).selectinload(DestinationPolicy.notifications),
                joinedload(TransferRequest.dest).joinedload(DestinationPolicy.target),
                joinedload(TransferRequest.current_state),
                selectinload(TransferRequest.states)
            )
            .where(
                or_(
                    TransferRequest.next_retry_min_time.is_(None),
                    TransferRequest.next_retry_min_time <= now
                )
            )
        )

        if state:
            query = query.where(State.state == state)
        if sub_state:
            query = query.where(State.sub_state == sub_state)
        if queues:
            query = query.where(Queue.name.in_(queues))
        if size is not None:
            query = query.where(
                or_(
                TransferRequest.size < size,
                TransferRequest.size.is_(None)
                )
            )
        query = query.with_for_update(of=TransferRequest, skip_locked=True)
        return self.session.scalar(query)
