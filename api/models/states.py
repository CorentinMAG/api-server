from __future__ import annotations
from ..db import Base as SQLBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, ForeignKey
from datetime import datetime
from sqlalchemy_serializer import SerializerMixin

class State(SQLBase, SerializerMixin):
    __tablename__ = "states"

    id: Mapped[int] = mapped_column(primary_key=True)
    state: Mapped[str] = mapped_column(String(10))
    date: Mapped[str] = mapped_column(DateTime, default=datetime.utcnow)
    request_id: Mapped[int] = mapped_column(ForeignKey("transfer_requests.id", ondelete="CASCADE"))