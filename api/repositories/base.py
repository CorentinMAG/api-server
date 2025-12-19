from typing import Generic, TypeVar
from sqlalchemy.orm import Session
from sqlalchemy import select, func, Select
from ..models.base import Base
from ..errors import NotFoundError
from flask_sqlalchemy import SQLAlchemy

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations"""

    def __init__(self, model: type[ModelType], db: SQLAlchemy):
        self._model = model
        self._db = db

    @property
    def session(self) -> Session:
        return self._db.session
    
    def get_by_id(self, id: int) -> ModelType:
        """get a single record by id"""
        obj = self._db.session.get(self._model, id)
        if not obj:
            raise NotFoundError(f"{self._model.__name__} with id {id} not found")
        return obj

    def get_all(self, skip: int = 0, limit: int = 100, filters: dict[str, any] | None = None) -> list[ModelType]:
        """get all records with optional filters"""
        query = select(self._model)

        if filters:
            query = self._filter(query, filters)

        query = query.offset(skip).limit(limit)
        return list(self._db.session.scalars(query).all())

    def _filter(self, query: Select, filters: dict[str, any]) -> Select:
        for key, value in filters.items():
            if hasattr(self._model, key) and value is not None:
                query = query.where(getattr(self._model, key) == value)
        return query

    def count(self, filters: dict[str, any] | None = None) -> int:
        """count records with optional filters"""
        query = select(func.count()).select_from(self._model)

        if filters:
            query = self._filter(query, filters)
        return self._db.session.scalar(query) or 0
    
    def create(self, obj: ModelType) -> ModelType:
        """create a new record"""

        self._db.session.add(obj)
        self._db.session.flush()
        return obj
    
    def update(self, obj: type[Base], data: dict[str, any]) -> ModelType:
        """update a record"""
        obj.update(data)
        self._db.session.flush()
        return obj
    
    def delete(self, obj: ModelType) -> None:
        """delete a record"""
        self._db.session.delete(obj)
        self._db.session.flush()