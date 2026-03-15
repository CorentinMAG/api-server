from __future__ import annotations
from flask.views import MethodView
from typing import Generic, TypeVar, ClassVar
from api.services.base import BaseService
from api.services import DTR_SERVICES
from flask import Blueprint
from abc import ABC, abstractmethod
from typing import get_type_hints
import inspect

Service = TypeVar("Service", bound=BaseService)


class BaseAPI(MethodView, ABC, Generic[Service]):
    init_every_request = False

    # each subclass implements their own router
    router: ClassVar[Blueprint | None] = None

    # prefix used in the path uri
    prefix: ClassVar[str | None] = None

    # If defined, the default routes (/, /<id>) will not be registered and only the custom routes defined in ROUTES (and eventually @route) will be registered
    ROUTES: ClassVar[list[dict]] = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        class_name = cls.__name__
        cls._service_name = class_name.replace("API", "Service")
        cls._register_routes()

    def __init__(self):
        service_name = getattr(self.__class__, "_service_name")
        self._service = BaseService._get_or_create_service(
            self._resolve_service_class(service_name) if service_name else None
        )

        # automatically inject required Service based on type annotations
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

    @classmethod
    def _register_routes(cls):
        """
        each subclass implements their own router `cls.router`

        regular methods get ,delete, put and post add automatically
        added to the router

        the @route(url, methods) decorator can be used to add
        custom routes
        """
        prefix = cls.prefix or cls.__name__.lower()[:-3]
        cls.router = Blueprint(prefix, __name__, url_prefix=prefix)

        # add custom routes to the router
        for name, method in inspect.getmembers(cls, inspect.isfunction):
            route_info = getattr(method, "_route", None)
            if not route_info:
                continue
            url = route_info["path"]
            methods = route_info["methods"]

            def make_view(method_name):

                def view(*args, **kwargs):
                    instance = cls()
                    handler = getattr(instance, method_name)
                    return handler(*args, **kwargs)

                return view

            cls.router.add_url_rule(url, view_func=make_view(name), methods=methods)
        view = cls.as_view(prefix)

        if cls.ROUTES:
            for route in cls.ROUTES:
                cls.router.add_url_rule(
                    route["rule"],
                    view_func=view,
                    methods=route["methods"],
                    strict_slashes=False,
                )
        else:

            # regular route registration
            cls.router.add_url_rule(
                "/", view_func=view, methods=["GET", "POST"], strict_slashes=False
            )
            cls.router.add_url_rule(
                "/<int:id>", view_func=view, methods=["GET", "PUT", "DELETE"]
            )

    @property
    def service(self) -> Service:
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
    def _resolve_service_class(service_name: str) -> Service | None:
        return DTR_SERVICES.get(service_name)

    @classmethod
    def register(cls, bp: Blueprint) -> None:
        subclasses = BaseAPI.__subclasses__()
        for subclass in subclasses:
            if subclass.router is not None:
                bp.register_blueprint(subclass.router)
