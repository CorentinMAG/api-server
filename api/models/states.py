from __future__ import annotations

from dtr_common.constantes import State as StateEnum, SubState as SubStateEnum
from sqlalchemy import ForeignKey, event, Connection, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_serializer import SerializerMixin

from .base import Base


class State(Base, SerializerMixin):
    __tablename__ = "states"

    serialize_only = ("state", "created_at", "failure_reason", "sub_state")

    state: Mapped[StateEnum] = mapped_column(index=True)
    failure_reason: Mapped[str | None]
    sub_state: Mapped[SubStateEnum | None] = mapped_column(default=None, index=True)

    request_id: Mapped[int] = mapped_column(
        ForeignKey("transfer_requests.id", ondelete="CASCADE"), index=True
    )

@event.listens_for(State, "after_insert")
def update_transfer_request_current_state_on_insert(mapper, connection: Connection, target: State):
  """update TransferRequest's current_state_id when a new state is inserted"""
  from .request import TransferRequest
  connection.execute(
     TransferRequest.__table__.update()
     .where(TransferRequest.id == target.request_id)
     .values(current_state_id = target.id)
  )

@event.listens_for(State, "after_delete")
def update_transfer_request_current_state_on_delete(mapper: any, connection: Connection, target: State):
   """recompute current_state_id when latest state is deleted"""

   from .request import TransferRequest
   
   latest_state_id = connection.execute(
      select(State.id)
      .where(State.id == target.request_id)
      .order_by(State.created_at.desc())
      .limit(1)
   ).scalar()

   connection.execute(
      TransferRequest.__table__.update()
      .where(TransferRequest.id == target.request_id)
      .values(current_state_id = latest_state_id)
   )