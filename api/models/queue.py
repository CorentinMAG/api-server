from __future__ import annotations
from ..db import Base as SQLBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer

class Queue(SQLBase):
    __tablename__ = "queue"
    queueid: Mapped[int] = mapped_column(primary_key=True)
    maxqueueditems = mapped_column(Integer)
    priorityorder = mapped_column(Integer)
    queuethreshold = mapped_column(Integer)
    transferworkerid = mapped_column(Integer)