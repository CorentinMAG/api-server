from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine
import sqlalchemy
import os

from ..db import Base as SQLBase


class Credentials(SQLBase, SerializerMixin):
    __tablename__ = "credentials"

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str]
    password: Mapped[str] = mapped_column(
        StringEncryptedType(sqlalchemy.CHAR, os.environ["DTR_ENCRYPTION_KEY"], AesEngine, "pkcs5"),
        nullable=False,
    )
    target_id: Mapped[int | None] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    server_id: Mapped[int | None] = mapped_column(ForeignKey("notification_servers.id", ondelete="CASCADE"))
