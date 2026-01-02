from .base import BaseModel
from .server import NotificationServer
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_serializer import SerializerMixin


class NotificationParameter(BaseModel, SerializerMixin):

    serialize_only = ()

    __tablename__ = "notification_parameters"

    type: Mapped[str]
    notification_id: Mapped[int] = mapped_column(
        ForeignKey("notifications.id", ondelete="CASCADE")
    )

    __mapper_args__ = {
        "polymorphic_identity": "notification_parameters",
        "polymorphic_on": "type",
    }


class KafkaParameters(NotificationParameter, SerializerMixin):
    __tablename__ = "kafka_parameters"

    __mapper_args__ = {"polymorphic_identity": "kafka"}

    serialize_only = ("topic", "replicas", "partitions")

    id: Mapped[int] = mapped_column(
        ForeignKey("notification_parameters.id"), primary_key=True
    )

    topic: Mapped[str]
    replicas: Mapped[int] = mapped_column(default=1)
    partitions: Mapped[int] = mapped_column(default=1)


class Notification(BaseModel, SerializerMixin):

    __tablename__ = "notifications"

    serialize_only = ("server", "parameters")

    server_id: Mapped[int] = mapped_column(
        ForeignKey("notification_servers.id", ondelete="CASCADE")
    )
    dest_id: Mapped[int] = mapped_column(
        ForeignKey("destination_policies.id", ondelete="CASCADE")
    )

    parameters: Mapped[list[NotificationParameter]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )
    server: Mapped[NotificationServer] = relationship()
