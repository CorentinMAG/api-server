"""
Additional SQLAlchemy model tests.

These tests cover default values and uniqueness constraints not exercised elsewhere.
"""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from api.models import GlobalParameters, NotificationServer, Target, TargetParameters
from tests.factories import GlobalParametersFactory, NotificationServerFactory, TargetFactory


class TestNotificationServerModel:
    def test_notification_server_name_unique(self, db_session):
        server_one = NotificationServerFactory.create(name="unique_server")
        db_session.add(server_one)
        db_session.commit()

        with pytest.raises(IntegrityError):
            server_two = NotificationServerFactory.create(name="unique_server")
            db_session.add(server_two)
            db_session.commit()

        db_session.rollback()


class TestGlobalParametersModel:
    def test_global_parameters_defaults(self, db_session):
        params = GlobalParametersFactory.create()
        db_session.add(params)
        db_session.commit()

        loaded = db_session.get(GlobalParameters, params.id)
        assert loaded is not None
        assert loaded.mode.value == "online"
        assert loaded.queue_limit == 100
        assert loaded.queue_threshold == 80


class TestTargetParametersModel:
    def test_target_parameters_linked_to_target(self, db_session):
        target = TargetFactory.create()
        db_session.add(target)
        db_session.commit()

        loaded_target = db_session.get(Target, target.id)
        assert loaded_target is not None
        assert isinstance(loaded_target.parameters, TargetParameters)
        assert loaded_target.parameters.target_id == loaded_target.id
