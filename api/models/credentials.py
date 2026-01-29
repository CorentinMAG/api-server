from __future__ import annotations

import sqlalchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

from ..config import ENCRYPTION_KEY
from .base import Base

class Credentials(Base, SerializerMixin):
    __tablename__ = "credentials"

    serialize_only = ("login", "password")

    login: Mapped[str] = mapped_column(index=True)
    password: Mapped[str] = mapped_column(
        StringEncryptedType(sqlalchemy.CHAR, ENCRYPTION_KEY, AesEngine, "pkcs5"),
        nullable=False,
    )

    # one to one relationship
    # ondelete=CASCADE means that database handle Credentials deletion
    # when the associated Target or NotificationServer object is deleted
    target_id: Mapped[int | None] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"), unique=True, index=True)
    server_id: Mapped[int | None] = mapped_column(ForeignKey("notification_servers.id", ondelete="CASCADE"), unique=True, index=True)
