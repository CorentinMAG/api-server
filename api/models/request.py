from __future__ import annotations
from ..db import Base as SQLBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, DateTime
from datetime import datetime
import uuid
from sqlalchemy_serializer import SerializerMixin

class TransferRequest(SQLBase, SerializerMixin):
    __tablename__ = "transfer_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(50))
    size: Mapped[int | None] = mapped_column(Integer)
    uid: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, unique=True)
    states: Mapped[list["State"]] = relationship()
    policy_id: Mapped[int] = mapped_column(ForeignKey("transfer_policies.id", ondelete="SET NULL"))
    policy: Mapped["TransferPolicy"] = relationship(back_populates="transfers")
    nb_retry: Mapped[int] = mapped_column(default=0)
    date: Mapped[str] = mapped_column(DateTime, default=datetime.utcnow)