"""
Test factories for creating mock objects for testing.

This module provides factory classes for creating test instances
of API models with realistic default values, making tests more
maintainable and readable.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from dtr_common.constantes import Protocol, State as StateEnum, Type

from api.models.credentials import Credentials
from api.models.parameters import (
    GlobalParameters,
    PeriodicalParameters,
    TargetParameters,
    TransferPolicyParameters,
)
from api.models.policies import DestinationPolicy, SourcePolicy, TransferPolicy
from api.models.queue import Queue
from api.models.request import TransferRequest
from api.models.server import NotificationServer
from api.models.states import State
from api.models.target import Target


class MockFactory:
    """Base factory with common utilities."""

    @staticmethod
    def fake_uuid() -> uuid.UUID:
        """Generate a fake UUID for testing."""
        return uuid.uuid4()

    @staticmethod
    def fake_datetime() -> datetime:
        """Generate a fake datetime for testing."""
        return datetime.utcnow()


class CredentialsFactory(MockFactory):
    """Factory for Credentials model"""

    @classmethod
    def create(cls, **kwargs) -> Credentials:
        defaults = {
            "login": "test_user",
            "password": "test_password",
        }
        defaults.update(kwargs)
        return Credentials(**defaults)


class TargetParametersFactory(MockFactory):
    """Factory for TargetParameters model"""

    @classmethod
    def create(cls, **kwargs) -> TargetParameters:
        defaults = {
            "use_ssl": True,
            "verify": True,
        }
        defaults.update(kwargs)
        return TargetParameters(**defaults)


class TargetFactory(MockFactory):
    """Factory for Target model"""

    @classmethod
    def create(cls, **kwargs) -> Target:
        defaults = {
            "name": f"test_target_{cls.fake_uuid()}",
            "protocol": Protocol.SFTP,
            "host": "test.example.com",
            "port": 22,
            "credentials": CredentialsFactory.create(),
            "parameters": TargetParametersFactory.create(),
        }
        defaults.update(kwargs)
        return Target(**defaults)

    @classmethod
    def create_sftp(cls, **kwargs) -> Target:
        defaults = {"protocol": Protocol.SFTP, "port": 22}
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def create_s3(cls, **kwargs) -> Target:
        defaults = {
            "protocol": Protocol.S3,
            "port": 443,
            "host": "s3.amazonaws.com",
        }
        defaults.update(kwargs)
        return cls.create(**defaults)


class GlobalParametersFactory(MockFactory):
    """Factory for GlobalParameters model"""

    @classmethod
    def create(cls, **kwargs) -> GlobalParameters:
        defaults = {
            "queue_timeout": 86400,
            "queue_limit": 100,
            "queue_threshold": 80,
            "polling_interval": 10,
            "max_retry": 5,
            "retry_delay": 300,
            "only_new_data": True,
            "transfer_timeout": 3600,
            "transfer_requests_history": 31,
        }
        defaults.update(kwargs)
        return GlobalParameters(**defaults)


class QueueFactory(MockFactory):
    """Factory for Queue model"""

    @classmethod
    def create(cls, **kwargs) -> Queue:
        defaults = {
            "name": f"test_queue_{cls.fake_uuid()}",
            "priority": 1,
            "queue_timeout": 3600,
            "queue_limit": 100,
            "queue_threshold": 80,
        }
        defaults.update(kwargs)
        return Queue(**defaults)


class NotificationServerFactory(MockFactory):
    """Factory for NotificationServer model"""

    @classmethod
    def create(cls, **kwargs) -> NotificationServer:
        defaults = {
            "name": "test_notification_server",
            "type": "kafka",
            "host": "kafka.example.com",
            "port": 9092,
            "credentials": CredentialsFactory.create(),
        }
        defaults.update(kwargs)
        return NotificationServer(**defaults)


class SourcePolicyFactory(MockFactory):
    """Factory for SourcePolicy model"""

    @classmethod
    def create(cls, **kwargs) -> SourcePolicy:
        defaults = {
            "path": "/source/path",
            "pattern": "*",
            "purge": False,
            "target": TargetFactory.create(),
        }
        defaults.update(kwargs)
        return SourcePolicy(**defaults)


class DestinationPolicyFactory(MockFactory):
    """Factory for DestinationPolicy model"""

    @classmethod
    def create(cls, **kwargs) -> DestinationPolicy:
        defaults = {
            "path": "/dest/path",
            "target": TargetFactory.create(),
        }
        defaults.update(kwargs)
        return DestinationPolicy(**defaults)


class PeriodicalParametersFactory(MockFactory):
    """Factory for PeriodicalParameters model"""

    @classmethod
    def create(cls, **kwargs) -> PeriodicalParameters:
        defaults = {
            "polling_interval": 60,
        }
        defaults.update(kwargs)
        return PeriodicalParameters(**defaults)


class TransferPolicyParametersFactory(MockFactory):
    """Factory for TransferPolicyParameters model"""

    @classmethod
    def create(cls, **kwargs) -> TransferPolicyParameters:
        defaults = {
            "max_retry": 5,
            "retry_delay": 300,
            "transfer_requests_history": 31,
            "only_new_data": True,
            "transfer_timeout": 3600,
        }
        defaults.update(kwargs)
        return TransferPolicyParameters(**defaults)


class TransferPolicyFactory(MockFactory):
    """Factory for TransferPolicy model"""

    @classmethod
    def create(cls, **kwargs) -> TransferPolicy:
        defaults = {
            "name": f"test_transfer_policy_{cls.fake_uuid()}",
            "type": Type.PERIODICAL,
            "enabled": True,
            "queue": QueueFactory.create(),
            "parameters": TransferPolicyParametersFactory.create(),
            "src": SourcePolicyFactory.create(),
            "dests": [],  # Will be set after policy creation to avoid circular dependency
        }
        defaults.update(kwargs)
        policy = TransferPolicy(**defaults)

        # Add destinations after policy creation if not provided
        if not kwargs.get("dests"):
            dest = DestinationPolicyFactory.create()
            policy.dests = [dest]

        return policy

    @classmethod
    def create_periodical(cls, **kwargs) -> TransferPolicy:
        params = TransferPolicyParametersFactory.create()
        params.periodical = PeriodicalParametersFactory.create()
        defaults = {
            "type": Type.PERIODICAL,
            "parameters": params,
        }
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def create_commanded(cls, **kwargs) -> TransferPolicy:
        defaults = {
            "type": Type.COMMANDED,
        }
        defaults.update(kwargs)
        return cls.create(**defaults)


class StateFactory(MockFactory):
    """Factory for State model"""

    @classmethod
    def create(cls, **kwargs) -> State:
        defaults = {
            "state": StateEnum.QUEUED,
            "failure_reason": None,
        }
        defaults.update(kwargs)
        return State(**defaults)

    @classmethod
    def create_queued(cls, **kwargs) -> State:
        defaults = {"state": StateEnum.QUEUED}
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def create_running(cls, **kwargs) -> State:
        defaults = {
            "state": StateEnum.RUNNING,
        }
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def create_successful(cls, **kwargs) -> State:
        defaults = {
            "state": StateEnum.SUCCESSFUL,
        }
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def create_failed(cls, **kwargs) -> State:
        defaults = {
            "state": StateEnum.FAILED,
            "failure_reason": "Connection timeout",
        }
        defaults.update(kwargs)
        return cls.create(**defaults)


class TransferRequestFactory(MockFactory):
    """Factory for TransferRequest model"""

    @classmethod
    def create(cls, **kwargs) -> TransferRequest:
        defaults = {
            "filename": "test_file.txt",
            "src_relative_path": "/source/test_file.txt",
            "policy": TransferPolicyFactory.create(),
            "size": 1.024,  # Size in MB (1024 bytes = ~1MB)
            "nb_retry": 0,
        }
        defaults.update(kwargs)
        return TransferRequest(**defaults)

    @classmethod
    def create_queued(cls, **kwargs) -> TransferRequest:
        # Note: State management is through states relationship, not a direct field
        defaults = {}
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def create_running(cls, **kwargs) -> TransferRequest:
        defaults = {}
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def create_successful(cls, **kwargs) -> TransferRequest:
        defaults = {}
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def create_failed(cls, **kwargs) -> TransferRequest:
        defaults = {
            "nb_retry": 1,
        }
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def create_large_file(cls, **kwargs) -> TransferRequest:
        defaults = {
            "filename": "large_file.dat",
            "size": 100.0,  # 100MB
        }
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def create_with_retries(cls, retries: int = 2, **kwargs) -> TransferRequest:
        defaults = {
            "nb_retry": retries,
        }
        defaults.update(kwargs)
        return cls.create(**defaults)


def create_test_scenario_basic() -> dict[str, Any]:
    """Create a basic test scenario with minimal data."""
    queue = QueueFactory.create()
    policy = TransferPolicyFactory.create(queue=queue)
    request = TransferRequestFactory.create(policy=policy)

    return {
        "queue": queue,
        "policy": policy,
        "request": request,
    }


def create_test_scenario_complex() -> dict[str, Any]:
    """Create a complex test scenario with multiple entities."""
    # Create multiple queues with different priorities
    high_priority_queue = QueueFactory.create(name="high_priority", priority=1)
    normal_priority_queue = QueueFactory.create(name="normal_priority", priority=5)
    low_priority_queue = QueueFactory.create(name="low_priority", priority=10)

    # Create multiple policies
    periodical_policy = TransferPolicyFactory.create_periodical(
        name="periodical_policy", queue=high_priority_queue
    )
    commanded_policy = TransferPolicyFactory.create_commanded(
        name="commanded_policy", queue=normal_priority_queue
    )

    # Create multiple requests in different states
    queued_request = TransferRequestFactory.create_queued(policy=periodical_policy)
    running_request = TransferRequestFactory.create_running(policy=commanded_policy)
    successful_request = TransferRequestFactory.create_successful(policy=periodical_policy)
    failed_request = TransferRequestFactory.create_failed(policy=commanded_policy)

    return {
        "queues": [high_priority_queue, normal_priority_queue, low_priority_queue],
        "policies": [periodical_policy, commanded_policy],
        "requests": [queued_request, running_request, successful_request, failed_request],
    }


class TestFactories:
    """Test utilities for creating test objects."""

    @staticmethod
    def create_credentials(**kwargs):
        return CredentialsFactory.create(**kwargs)

    @staticmethod
    def create_queue(**kwargs):
        return QueueFactory.create(**kwargs)

    @staticmethod
    def create_transfer_request(**kwargs):
        return TransferRequestFactory.create(**kwargs)
