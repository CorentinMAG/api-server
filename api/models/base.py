from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), index=True)
    updated_at: Mapped[datetime | None] = mapped_column(default=None, onupdate=func.now())

    def __repr__(self) -> str:
        return self.__str__()
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({','.join(f'{c.name}={getattr(self, c.name)}' for c in self.__table__.columns)})"
    
    def update(self, data: dict[str, any]) -> None:
        """update model attributes from a dictionnary"""
        for key, value in data.items():
            if hasattr(self, key) and key not in ("id", "created_at", "updated_at", "uid"):
                # handle nested relationships
                if key in self.__mapper__.relationships:
                    relation = getattr(self, key)
                    if relation is not None and isinstance(value, dict):
                        relation.update(value)
                    continue
                # handle regular columns
                if key in self.__mapper__.column_attrs:
                    setattr(self, key, value)
