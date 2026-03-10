from __future__ import annotations

from sqlalchemy import Connection, ForeignKey, event
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_serializer import SerializerMixin

from api.dtr_common.constantes import State as StateEnum, SubState as SubStateEnum

from .base import BaseModel


class State(BaseModel, SerializerMixin):
    __tablename__ = "states"

    serialize_only = ("state", "created_at", "failure_reason", "sub_state")

    state: Mapped[StateEnum] = mapped_column(index=True)
    failure_reason: Mapped[str | None]
    sub_state: Mapped[SubStateEnum | None] = mapped_column(default=None, index=True)

    request_id: Mapped[int] = mapped_column(
        ForeignKey("transfer_requests.id", ondelete="CASCADE"), index=True
    )


@event.listens_for(State, "after_insert")
def update_transfer_request_current_state_on_insert(mapper: any, connection: Connection, target: State):
    """
    Automatically update the parent TransferRequest's current_state when a new State is inserted
    """
    from .request import TransferRequest

    connection.execute(
        TransferRequest.__table__.update()
        .where(TransferRequest.id == target.request_id)
        .values(current_state_id=target.id)
    )


@event.listens_for(State, "after_delete")
def update_transfer_request_current_state_on_delete(mapper: any, connection: Connection, target: State):
    """
    Automatically update the parent TransferRequest's current_state when a State is deleted
    """
    from sqlalchemy import desc, select

    from .request import TransferRequest

    # Find the latest state for the request, if any
    latest_state_id = connection.execute(
        select(State.id)
        .where(State.request_id == target.request_id)
        .order_by(desc(State.created_at))
        .limit(1)
    ).scalar()

    # Update the TransferRequest's current_state_id
    connection.execute(
        TransferRequest.__table__.update()
        .where(TransferRequest.id == target.request_id)
        .values(current_state_id=latest_state_id)
    )
