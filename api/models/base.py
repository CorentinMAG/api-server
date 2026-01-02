from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import func
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.engine import Engine


@event.listens_for(Engine, "connect")
def enable_fk(dbapi_con, _):
    if dbapi_con.__class__.__module__.startswith("sqlite3"):
        cursor = dbapi_con.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class Base(DeclarativeBase):
    pass


class BaseModel(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(onupdate=func.now())

    def update(self, data: dict[str, any]) -> None:
        """Update model attributes from a dictionary"""
        for key, value in data.items():
            if key in self.__mapper__.column_attrs.keys():
                setattr(self, key, value)
            elif key in self.__mapper__.relationships.keys():
                relation = getattr(self, key)
                if relation is not None and isinstance(value, dict):
                    relation.update(value)

    def __str__(self):
        return f"{self.__class__.__name__}: {", ".join([f"{c.key}:{getattr(self, c.key)}" for c in self.__class__.__mapper__.column_attrs])}"

    def __repr__(self):
        return self.__str__()
