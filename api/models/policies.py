from __future__ import annotations
from ..db import Base as SQLBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Table, Column

assocation_table = Table(
    "association_table",
    SQLBase.metadata,
    Column("transfer_policy_id", ForeignKey("transfer_policies.id")),
    Column("queue_id", ForeignKey("queues.id"))
)

association_table2 = Table(
    "policy_server",
    SQLBase.metadata,
    Column("transfer_policy_id", ForeignKey("transfer_policies.id")),
    Column("notification_servers.id", ForeignKey("notification_servers.id"))
)

class TransferPolicy(SQLBase):
    __tablename__ = "transfer_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique = True)
    enabled: Mapped[bool] = mapped_column(default = True)
    type: Mapped[str]

    servers: Mapped[list["NotificationServer"]] = relationship(secondary=association_table2)

    src: Mapped["SourcePolicy"] = relationship()
    src_id: Mapped[int] = mapped_column(ForeignKey("source_policies.id", ondelete="CASCADE"))

    dest: Mapped["DestinationPolicy"] = relationship()
    dest_id: Mapped[int] = mapped_column(ForeignKey("destination_policies.id", ondelete="CASCADE"))

    parameters: Mapped["TransferParameters"] = relationship()
    queues: Mapped[list["Queue"]] = relationship(secondary=assocation_table)
    transfers: Mapped[list["TransferRequest"]] = relationship()


class SourcePolicy(SQLBase):
    __tablename__ = "source_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    purge: Mapped[bool] = mapped_column(default=False)
    path: Mapped[str | None]

    src_id: Mapped[int] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    src: Mapped["Target"] = relationship()

class DestinationPolicy(SQLBase):
    __tablename__ = "destination_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str | None]

    dest_id: Mapped[int] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    dest: Mapped["Target"] = relationship()
