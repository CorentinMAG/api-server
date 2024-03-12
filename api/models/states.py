from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_serializer import SerializerMixin

from ..db import Base as SQLBase


class State(SQLBase, SerializerMixin):
    __tablename__ = "states"

    id: Mapped[int] = mapped_column(primary_key=True)
    state: Mapped[str]
    created_at: Mapped[str] = mapped_column(DateTime, default=datetime.utcnow)
    request_id: Mapped[int] = mapped_column(ForeignKey("transfer_requests.id", ondelete="CASCADE"))
    reason: Mapped[str | None]
