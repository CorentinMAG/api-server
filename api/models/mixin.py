from sqlalchemy.event import listens_for
from sqlalchemy import select, Connection
from sqlalchemy.orm import Session
from .base import Base
from .parameters import GlobalParameters


class ParametersConfigMixin:
    """
    A mixin for applying default values from global parameters to model instances.
    """

    def __new__(cls, *args, **kwargs):
        cls.register_inheritance_hook()
        return super().__new__(cls)

    @classmethod
    def register_inheritance_hook(cls):
        @listens_for(cls, "before_insert", propagate=True)
        def on_before_insert(mapper, connection: Connection, target):
            cls._apply_defaults(target, connection)

        @listens_for(cls, "before_update", propagate=True)
        def on_before_update(mapper, connection: Connection, target):
            cls._apply_defaults(target, connection)

    @classmethod
    def _apply_defaults(cls, target: Base, connection: Connection):

        with Session(bind=connection) as session:
            parameters = session.scalar(select(GlobalParameters).limit(1))

        dest_fields = set([c.name for c in target.__table__.columns])
        src_fields = set([c.name for c in parameters.__table__.columns])

        common_fields = dest_fields.intersection(src_fields)

        # discard common fields that must not be
        # used as default values
        common_fields.discard("id")
        common_fields.discard("created_at")
        common_fields.discard("updated_at")

        for c in common_fields:
            if getattr(target, c) is None:
                value = getattr(parameters, c)
                setattr(target, c, value)
