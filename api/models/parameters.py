from __future__ import annotations

from typing import TYPE_CHECKING

from api.dtr_common.constantes import Mode
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin

from .base import BaseModel

if TYPE_CHECKING:
    from .server import NotificationServer


class TransferPolicyParameters(BaseModel, SerializerMixin):
    __tablename__ = "transfer_policy_parameters"

    serialize_only = (
        "max_retry",
        "retry_delay",
        "transfer_requests_history",
        "only_new_data",
        "transfer_timeout",
    )

    max_retry: Mapped[int | None]
    retry_delay: Mapped[int | None] = mapped_column(comment="in seconds")
    transfer_requests_history: Mapped[int | None]
    only_new_data: Mapped[bool | None]
    transfer_timeout: Mapped[int | None] = mapped_column(comment="in seconds")

    policy_id: Mapped[int] = mapped_column(
        ForeignKey("transfer_policies.id", ondelete="CASCADE"), unique=True
    )


class GlobalParameters(BaseModel, SerializerMixin):
    __tablename__ = "global_parameters"

    serialize_only = (
        "mode",
        "tmp_prefix",
        "final_prefix",
        "retry_delay",
        "max_retry",
        "transfer_requests_history",
        "only_new_data",
        "transfer_timeout",
        "queue_timeout",
        "polling_interval",
        "queue_limit",
        "queue_threshold",
    )

    mode: Mapped[Mode] = mapped_column(default=Mode.ONLINE)
    tmp_prefix: Mapped[str | None]
    final_prefix: Mapped[str | None]
    retry_delay: Mapped[int | None] = mapped_column(default=300, comment="in seconds")
    max_retry: Mapped[int | None] = mapped_column(default=5)
    transfer_requests_history: Mapped[int] = mapped_column(default=31)
    only_new_data: Mapped[bool] = mapped_column(default=True)
    transfer_timeout: Mapped[int] = mapped_column(default=3600, comment="in seconds")
    queue_timeout: Mapped[int] = mapped_column(default=86400, comment="in seconds")
    polling_interval: Mapped[int] = mapped_column(default=10, comment="in seconds")
    queue_limit: Mapped[int] = mapped_column(default=100)
    queue_threshold: Mapped[int] = mapped_column(default=80)


class TargetParameters(BaseModel, SerializerMixin):
    __tablename__ = "target_parameters"

    serialize_only = ("use_ssl", "verify")

    use_ssl: Mapped[bool] = mapped_column(default=True)
    verify: Mapped[bool] = mapped_column(default=True)
    target_id: Mapped[int] = mapped_column(
        ForeignKey("targets.id", ondelete="CASCADE"), unique=True, index=True
    )

    def to_dict(self) -> dict[str, bool]:
        return {
            "use_ssl": self.use_ssl,
            "verify": self.verify,
        }
