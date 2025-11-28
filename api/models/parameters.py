from __future__ import annotations

from typing import TYPE_CHECKING
import sqlalchemy
from dtr_common.constantes import Mode
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine
from .base import Base
from ..config import ENCRYPTION_KEY

if TYPE_CHECKING:
    from .server import NotificationServer

class TransferPolicyParameters(Base, SerializerMixin):
    __tablename__ = "transfer_policy_parameters"

    serialize_only = (
        "retry_delay",
        "transfer_timeout"
    )

    max_retry: Mapped[int | None]
    retry_delay: Mapped[int | None]  # in seconds
    transfer_requests_history: Mapped[int | None]
    only_new_data: Mapped[bool | None]
    transfer_timeout: Mapped[int | None]  # in seconds

    policy_id: Mapped[int] = mapped_column(ForeignKey("transfer_policies.id", ondelete="CASCADE"))

class GlobalParameters(Base, SerializerMixin):
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
    retry_delay: Mapped[int | None] = mapped_column(default=300)  # in seconds
    max_retry: Mapped[int | None] = mapped_column(default=5)
    transfer_requests_history: Mapped[int] = mapped_column(default=31)
    only_new_data: Mapped[bool] = mapped_column(default=True)
    transfer_timeout: Mapped[int] = mapped_column(default=3600)  # in seconds
    queue_timeout: Mapped[int] = mapped_column(default=86400)  # in seconds
    polling_interval: Mapped[int] = mapped_column(default=10)  # in seconds
    queue_limit: Mapped[int] = mapped_column(default=100)
    queue_threshold: Mapped[int] = mapped_column(default=80)


class TargetParameters(Base, SerializerMixin):
    __tablename__ = "target_parameters"

    serialize_only = ("use_ssl", "verify", "http_proxy", "https_proxy")

    use_ssl: Mapped[bool] = mapped_column(default=True)
    verify: Mapped[bool] = mapped_column(default=True)
    http_proxy: Mapped[str | None] = mapped_column(
        StringEncryptedType(sqlalchemy.CHAR, ENCRYPTION_KEY, AesEngine, "pkcs5"),
        nullable=True,
    )
    https_proxy: Mapped[str | None] = mapped_column(
        StringEncryptedType(sqlalchemy.CHAR, ENCRYPTION_KEY, AesEngine, "pkcs5"),
        nullable=True,
    )
    target_id: Mapped[int] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))

class ServerParameters(Base):
    __tablename__ = "server_parameters"

    type: Mapped[str]  # discriminator column to differentiate parameter types
    dest_id: Mapped[int] = mapped_column(ForeignKey("destination_policies.id", ondelete="CASCADE"))

    __mapper_args__ = {"polymorphic_identity": "transfer_parameters", "polymorphic_on": "type"}


class KafkaTopicParameters(ServerParameters, SerializerMixin):
    __tablename__ = "kafka_topic_parameters"

    serialize_only = ("topic", "replica", "partitions", "server")

    id: Mapped[int] = mapped_column(ForeignKey("server_parameters.id", ondelete="CASCADE"), primary_key=True)
    topic: Mapped[str]
    replica: Mapped[int | None] = mapped_column(default=1)
    partitions: Mapped[int | None] = mapped_column(default=1)
    server_id: Mapped[int] = mapped_column(ForeignKey("notification_servers.id", ondelete="CASCADE"))
    server: Mapped[NotificationServer] = relationship()

    __mapper_args__ = {"polymorphic_identity": "kafka_topic_parameters"}
