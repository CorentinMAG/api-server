from typing import Generic, TypeVar, ClassVar, cast, Iterable
from sqlalchemy.orm import Session
from flask import g
from sqlalchemy import select, func, Select, text
from api.exception import NotFoundException
from abc import ABC, abstractmethod
from api.models import DTR_MODELS
from api.models.base import Base
from werkzeug.datastructures import ImmutableMultiDict
from dtr_common.schema.pagination import Pagination, PaginationItem
from api.exception import MalformatedInputException

Model = TypeVar("Model", bound=Base)


class BaseRepository(Generic[Model], ABC):
    """
    Base repository with common CRUD operations
    A Repository flush database operations
    The commit happens at the controller level
    """

    _model_name: ClassVar[str | None]

    def __init_subclass__(cls: type["BaseRepository"], **kwargs):
        """
        hook that get triggered when subclasses are registered by the
        python interpreter
        allow us to customize subclasses
        Here, we fetch the model name from subclasses name
        """
        super().__init_subclass__(**kwargs)
        repository_name = cls.__name__
        if repository_name.endswith("Repository"):
            cls._model_name = repository_name[:-10]
        else:
            cls._model_name = None

    def __init__(self):
        model_name = getattr(self.__class__, "_model_name", None)
        if model_name:
            self._model = self._resolve_model_class(model_name)

    @property
    def model(self) -> type[Model]:
        return self._model

    @staticmethod
    def _resolve_model_class(model_name: str) -> type[Model]:
        return DTR_MODELS.get(model_name)

    @property
    def session(self) -> Session:
        return cast(Session, g.db_session)

    def base_query(self, eager=None) -> Select:
        query = select(self._model)
        if eager:
            query = query.options(*eager)
        return query

    def get_by_id(self, id: int, eager=None) -> Model:
        """get a single record by id"""
        query = self.base_query(eager=eager).where(self._model.id == id)
        obj = self.session.scalar(query)
        if not obj:
            raise NotFoundException(f"{self._model.__name__} with id {id} not found")
        return obj

    def get_by_name(self, name: str, eager=None) -> Model:
        """get a single record by its name"""
        query = self.base_query(eager=eager).where(self._model.name == name)
        obj = self.session.scalar(query)
        if not obj:
            raise NotFoundException(
                f"{self._model.__name__} with name {name} not found"
            )
        return obj

    def get_all(
        self,
        skip: int,
        limit: int,
        filters: dict[str, any] | None,
        eager,
    ) -> list[Model]:
        """
        get paginated records with optional filters
        """
        query = self.base_query(eager=eager)

        if filters:
            query = self._model.apply_filter(filters)

        query = query.offset(skip).limit(limit)
        return list(self.session.scalars(query).all())

    def count(self, filters: dict[str, any] | None = None) -> int:
        """count records with optional filters"""
        query = self.base_query(None)
        if filters:
            query = self._model.apply_filter(filters)
        count_query = select(func.count()).select_from(query.subquery())
        return self.session.scalar(count_query) or 0

    def create(self, obj: Model) -> Model:
        """create a new record"""
        try:
            self.session.add(obj)
            self.session.flush()
            return obj
        except:
            self.session.rollback()
            raise

    def paginate(
        self, args: ImmutableMultiDict, eager: Iterable | None
    ) -> Pagination[Model]:
        filters = args.to_dict()
        try:
            page = int(filters.pop("page", 1))
            page_size = int(filters.pop("page_size", 10))
        except ValueError as e:
            raise MalformatedInputException(
                "pagination parameters page or page_size are not integer"
            ) from e
        skip = (page - 1) * page_size
        items = self.get_all(skip=skip, limit=page_size, filters=filters, eager=eager)
        total = self.count(filters=filters)
        return Pagination(
            pagination=PaginationItem(page=page, page_size=page_size, total=total),
            items=items,
        )

    def update(self, obj: Model, data: dict[str, any]) -> Model:
        """update a record"""
        obj.update(data)
        self.session.flush()
        return obj

    def delete(self, obj: Model) -> None:
        """delete a record"""
        self.session.delete(obj)
        self.session.flush()

    def delete_all(self) -> None:
        """truncate the table"""
        sql = text(
            f"TRUNCATE TABLE {self._model.__tablename__} RESTART IDENTITY CASCADE"
        )
        self.session.execute(sql)
        self.session.flush()
