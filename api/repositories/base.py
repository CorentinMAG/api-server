from typing import Generic, TypeVar, ClassVar
from sqlalchemy.orm import Session
from flask import g
from sqlalchemy import select, func, Select, text
from api.exception import NotFoundException
from abc import ABC, abstractmethod
from api.models import DTR_MODELS
from werkzeug.datastructures import ImmutableMultiDict
from pydantic import BaseModel, ConfigDict
T = TypeVar("T")

class PaginationItem(BaseModel):
    page: int
    page_size: int
    total: int

class Pagination(BaseModel, Generic[T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    pagination: PaginationItem
    items: list[T]

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType], ABC):
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
            cls._model_name = repository_name[:10]
        else:
            cls._model_name = None

    def __init__(self):
        model_name = getattr(self.__class__, "_model_name", None)
        if model_name:
            self._model = self._resolve_model_class(model_name)

    @property
    def model(self) -> ModelType:
        return self._model

    @staticmethod
    def _resolve_model_class(model_name: str) -> ModelType:
        return DTR_MODELS.get(model_name)

    @property
    def session(self) -> Session:
        return g.db_session
    
    def get_by_id(self, id: int) -> ModelType:
        """get a single record by id"""
        obj = self.session.get(self._model, id)
        if not obj:
            raise NotFoundException(f"{self._model.__name__} with id {id} not found")
        return obj

    def get_all(
            self, 
            skip: int = 0, 
            limit: int = 100, 
            filters: dict[str, any] | None = None
        ) -> list[ModelType]:
        """
        get all records with optional filters  
        All relationships are lazy loaded by default  
        Implements the get_with_relations methods if  
        you want others loading strategies
        """
        query = select(self._model)

        if filters:
            query = self._filter(query, filters)

        query = query.offset(skip).limit(limit)
        return list(self.session.scalars(query).all())

    def _filter(self, query: Select, filters: dict[str, any]) -> Select:
        for key, value in filters.items():
            if hasattr(self._model, key) and value is not None:
                query = query.where(getattr(self._model, key) == value)
        return query
    
    @abstractmethod
    def get_with_relations(
        self,
        skip: int,
        limit: int,
        filters: dict[str, any] | None = None
    ) -> list[ModelType]:
        """
        This method is an equivalent of the get_all method
        but subclasses are free to implement their own loading strategies
        """
        pass

    def count(self, filters: dict[str, any] | None = None) -> int:
        """count records with optional filters"""
        query = select(func.count()).select_from(self._model)

        if filters:
            query = self._filter(query, filters)
        return self.session.scalar(query) or 0
    
    def create(self, obj: ModelType) -> ModelType:
        """create a new record"""
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
        items = self.get_with_relations(skip = skip, limit = page_size, filters = _args)
        total = self.count(filters=args.to_dict())
        return Pagination(
            pagination=PaginationItem(page = page, page_size=page_size, total = total, items = items)
        )

    
    def update(self, obj: ModelType, data: dict[str, any]) -> ModelType:
        """update a record"""
        obj.update(data)
        self.session.flush()
        return obj
    
    def delete(self, obj: ModelType) -> None:
        """delete a record"""
        self.session.delete(obj)
        self.session.flush()

    def delete_all(self) -> None:
        """truncate the table"""
        sql = text(f"TRUNCATE TABLE {self._model.__tablename__} RESTART IDENTITY CASCADE")
        self.session.execute(sql)
        self.session.flush()