from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypedDict, TypeVar, get_type_hints, ClassVar, cast

from flask import Blueprint
from flask.views import MethodView

from api.services import DTR_SERVICES
from api.services.base import BaseService

T = TypeVar("T", bound=BaseService)


class RouteRule(TypedDict):
    route: str
    methods: list[str]
    defaults: dict[str, any] | None


class BaseAPI(MethodView, ABC, Generic[T]):
    _service_instances: ClassVar[dict[str, BaseService]] = {}
    _service_name: ClassVar[str | None] = None

    prefix: ClassVar[str | None] = None
    custom_routes: ClassVar[dict[str, tuple[str, list[str]]]] = {}

    router: ClassVar[Blueprint | None] = None
    init_every_request = False

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        service_name = cls.__name__
        cls._service_name = service_name.replace("API", "Service")

    def __init__(self):
        service_name = cast(str | None, getattr(self.__class__, "_service_name"))
        self._service = (
            BaseService._get_or_create_service(
                self._resolve_service_class(service_name)
            )
            if service_name
            else None
        )

        try:
            hints = get_type_hints(self.__class__)
        except Exception:
            hints = self.__class__.__annotations__

        for attr_name, attr_type in hints.items():
            if (
                isinstance(attr_type, type)
                and issubclass(attr_type, BaseService)
                and attr_type is not BaseService
            ):
                setattr(self, attr_name, BaseService._get_or_create_service(attr_type))
        self._register_routes()

    def _register_routes(self):
        prefix = self.prefix or self.__class__.__name__.lower()
        self.router = Blueprint(prefix, __name__, url_prefix=prefix)

        view = self.__class__.as_view(prefix)

        self.router.add_url_rule("/", view_func=view, methods=["GET", "POST"])
        self.router.add_url_rule(
            "/<int:id>", view_func=view, methods=["GET", "PUT", "DELETE"]
        )

        for fn_name, (route, methods) in self.custom_routes.items():
            if not hasattr(self, fn_name):
                raise ValueError(
                    f"Custom route function '{fn_name}' not found in {self.__class__.__name__}"
                )
            view_func = getattr(self, fn_name)
            self.router.add_url_rule(route, view_func=view_func, methods=methods)

    @property
    def service(self) -> T:
        return self._service

    @abstractmethod
    def post(self):
        pass

    @abstractmethod
    def put(self, id: int):
        pass

    @abstractmethod
    def get(self, id: int | None = None):
        pass

    @abstractmethod
    def delete(self, id: int):
        pass

    @staticmethod
    def _resolve_service_class(service_name: str) -> T | None:
        return DTR_SERVICES.get(service_name)

    @classmethod
    def register(cls, bp: Blueprint) -> None:
        subclasses = BaseService.__subclasses__()
        for subclass in subclasses:
            if subclass.router is not None:
                bp.register_blueprint(subclass.router)
