from flask.views import MethodView
from typing import Generic, TypeVar, TypedDict
from api.services.base import BaseService
from api.services import DTR_SERVICES
from flask import Blueprint
from abc import ABC, abstractmethod

T = TypeVar("T")


class RouteRule(TypedDict):
    route: str
    methods: list[str]
    defaults: dict[str, any] | None


class BaseAPI(MethodView, ABC, Generic[T]):
    _service_instances: dict[str, BaseService] = {}
    service_name: str | None
    init_every_request = False

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        service_name = cls.__name__
        cls._service_name = service_name.replace("API", "Service")

    def __init__(self):
        service_name = getattr(self.__class__, "_service_name")
        self._service = self._get_or_create_service(service_name)

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

    @classmethod
    def _get_or_create_service(cls, service_name: str) -> T:
        if service_name not in cls._service_instances:
            service_class = cls._resolve_service_class(service_name)
            if not service_class:
                raise ValueError(f"Service with name {service_name} not found")
            cls._service_instances[service_name] = service_class()
        return cls._service_instances[service_name]

    @staticmethod
    def _resolve_service_class(service_name: str) -> T | None:
        return DTR_SERVICES.get(service_name)

    @classmethod
    def register(
        cls, name: str, url_prefix: str | None, rules: list[RouteRule]
    ) -> Blueprint:
        bp = Blueprint(name, __name__, url_prefix=url_prefix)
        view = cls.as_view(name)

        for route in rules:
            bp.add_url_rule(
                route["route"],
                view_func=view,
                methods=route.get("methods", ["GET", "POST", "PUT", "DELETE"]),
                defaults=route.get("defaults", {}),
                strict_slashes=False
            )
        return bp