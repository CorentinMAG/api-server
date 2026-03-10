from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from flask import g
from sqlalchemy import Select, func, select, text
from sqlalchemy.orm import Session
from werkzeug.datastructures import ImmutableMultiDict

from api.dtr_common.schema.pagination import Pagination, PaginationItem
from api.exceptions import NotFoundException
from api.models import DTR_MODELS, Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType], ABC):
    """Base repository with common CRUD operations"""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        repository_name = cls.__name__
        if repository_name.endswith("Repository"):
            cls._model_name = repository_name[:-10]
        else:
            cls._model_name = None

    def __init__(self) -> None:
        model_name = getattr(self.__class__, "_model_name", None)
        if model_name:
            self.model = self._resolve_model_class(model_name)

    @staticmethod
    def _resolve_model_class(model_name: str) -> ModelType:
        return DTR_MODELS.get(model_name)

    @property
    def session(self) -> Session:
        return g.db_session

    def get_by_id(self, id: int) -> ModelType:
        obj = self.session.get(self.model, id)
        if not obj:
            raise NotFoundException(f"{self.model.__name__} with id {id} not found")
        return obj

    def get_all(
        self, skip: int = 0, limit: int = 100, filters: dict[str, any] | None = None
    ) -> list[ModelType]:
        """get all records with optional filters"""
        query = select(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.where(getattr(self.model, key) == value)
        query = query.offset(skip).limit(limit)
        return list(self.session.scalars(query).all())

    def count(self, filters: dict[str, any] | None = None) -> int:
        """count records with optional filters"""
        query = select(func.count()).select_from(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.where(getattr(self.model, key) == value)
        return self.session.scalar(query) or 0

    def create(self, obj: ModelType) -> ModelType:
        """Create a new record"""
        try:
            self.session.add(obj)
            self.session.flush()
            return obj
        except:
            self.session.rollback()
            raise

    def paginate(self, args: ImmutableMultiDict) -> Pagination[ModelType]:
        _args = args.to_dict()
        page = int(_args.pop("page", 1))
        page_size = int(_args.pop("page_size", 10))
        skip = (page - 1) * page_size
        items = self.get_with_relations(skip=skip, limit=page_size, filters=_args)
        total = self.count(filters=args)
        return Pagination(
            pagination=PaginationItem(page=page, page_size=page_size, total=total),
            items=items,
        )

    @abstractmethod
    def get_with_relations(
        skip: int, limit: int, filters: dict[str, any] | None = None
    ):
        pass

    def filters(self, query: Select, filters: dict[str, any]):
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.where(getattr(self.model, key) == value)

    def update(self, obj: ModelType, data: dict[str, any]) -> ModelType:
        """Update a record"""
        obj.update(data)
        self.session.flush()
        return obj

    def delete(self, obj: ModelType) -> None:
        """delete a record"""
        self.session.delete(obj)
        self.session.flush()

    def delete_all(self) -> None:
        """truncate the table"""
        sql = text(
            f"TRUNCATE TABLE {self.model.__tablename__} RESTART IDENTITY CASCADE"
        )
        self.session.execute(sql)
        self.session.flush()
