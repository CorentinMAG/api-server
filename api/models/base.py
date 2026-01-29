from sqlalchemy import func, event, Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

@event.listens_for(Engine, "connect")
def enable_fx(dbapi_connection, _):
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        # the sqlite3 driver will not set PRAGMA foreign_keys
        # if autocommit=False; set to True temporarily
        # The autocommit property doesn't exist in python3.10 (need python>=3.12)
        #ac = dbapi_connection.autocommit
        #dbapi_connection.autocommit = True
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

        # restore previous autocommit setting
        #dbapi_connection.autocommit = ac


class Base(DeclarativeBase):

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), index=True)
    updated_at: Mapped[datetime | None] = mapped_column(default=None, onupdate=func.now())

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: ({', '.join([f'{c.key}={getattr(self, c.key)}' for c in self.__table__.columns])}"

    def update(self, data: dict[str, any]) -> None:
        """update model attributes from a dictionnary"""
        for key, value in data.items():
            if hasattr(self, key) and key not in ("id", "created_at", "updated_at", "uid"):
                # handle nested relationships
                if key in self.__mapper__.relationships.keys():
                    relation = getattr(self, key)
                    if relation is not None and isinstance(value, dict):
                        relation.update(value)
                    continue
                # handle regular columns
                if key in self.__mapper__.column_attrs.keys():
                    setattr(self, key, value)
