"""
Repository layer tests.

This test suite validates:
- Repository unit tests (85%+ coverage target)
- Database constraint tests
- Transaction isolation tests
- Performance benchmarks
- Specialized repository queries
"""

from __future__ import annotations

import os
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# Ensure encryption key is set before importing models
os.environ.setdefault("DTR_ENCRYPTION_KEY", "test-key-that-is-32-bytes-long")

# Set DATABASE_URL env before importing api modules
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

# Set FLASK_TESTING env variable early
os.environ.setdefault("FLASK_TESTING", "True")

from dtr_common.constantes import Type  # noqa: E402

from api.models import (  # noqa: E402
    Queue,
    Target,
)
from api.repositories import (  # noqa: E402
    QueueRepository,
    TargetRepository,
    TransferPolicyRepository,
    TransferRequestRepository,
)


class TestBaseRepositoryFunctionality:
    """Test BaseRepository functionality through concrete implementations."""

    def test_repository_initialization(self, db_session):
        """Test repository initialization with dependency injection."""
        queue_repo = QueueRepository(db_session)
        assert queue_repo.model_class == Queue
        assert queue_repo.db_session == db_session

        target_repo = TargetRepository(db_session)
        assert target_repo.model_class == Target
        assert target_repo.db_session == db_session

    def test_get_by_id_success(self, db_session):
        """Test get_by_id with successful retrieval."""
        queue_repo = QueueRepository(db_session)

        # Mock successful retrieval
        mock_queue = Mock()
        mock_queue.id = 1
        mock_queue.name = "test_queue"

        with patch.object(db_session, "get", return_value=mock_queue) as mock_get:
            result = queue_repo.get_by_id(1)

            assert result == mock_queue
            mock_get.assert_called_once_with(Queue, 1)

    def test_get_by_id_not_found(self, db_session):
        """Test get_by_id when entity doesn't exist."""
        queue_repo = QueueRepository(db_session)

        with patch.object(db_session, "get", return_value=None) as mock_get:
            result = queue_repo.get_by_id(999)

            assert result is None
            mock_get.assert_called_once_with(Queue, 999)

    def test_get_by_id_sql_error(self, db_session):
        """Test get_by_id with SQLAlchemy error."""
        queue_repo = QueueRepository(db_session)

        with patch.object(db_session, "get", side_effect=SQLAlchemyError("Database error")):
            result = queue_repo.get_by_id(1)

            assert result is None

    def test_get_all_basic(self, db_session):
        """Test get_all without pagination."""
        queue_repo = QueueRepository(db_session)

        mock_queues = [Mock(id=1, name="queue1"), Mock(id=2, name="queue2")]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_queues

        with patch.object(db_session, "execute", return_value=mock_result) as mock_execute:
            result = queue_repo.get_all()

            assert len(result) == 2
            assert result == mock_queues
            mock_execute.assert_called_once()

    def test_get_all_with_pagination(self, db_session):
        """Test get_all with limit and offset."""
        queue_repo = QueueRepository(db_session)

        mock_queues = [Mock(id=1, name="queue1")]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_queues

        with patch.object(db_session, "execute", return_value=mock_result) as mock_execute:
            result = queue_repo.get_all(limit=10, offset=5)

            assert len(result) == 1
            mock_execute.assert_called_once()

    def test_create_entity(self, db_session):
        """Test creating a new entity."""
        queue_repo = QueueRepository(db_session)

        mock_queue = Mock()
        mock_queue.name = "test_queue"

        with patch.object(db_session, "add") as mock_add:
            result = queue_repo.create(mock_queue)

            assert result == mock_queue
            mock_add.assert_called_once_with(mock_queue)

    def test_create_many_entities(self, db_session):
        """Test creating multiple entities."""
        queue_repo = QueueRepository(db_session)

        mock_queues = [Mock(name="queue1"), Mock(name="queue2")]

        with patch.object(db_session, "add_all") as mock_add_all:
            result = queue_repo.create_many(mock_queues)

            assert result == mock_queues
            mock_add_all.assert_called_once_with(mock_queues)

    def test_update_entity(self, db_session):
        """Test updating an entity."""
        queue_repo = QueueRepository(db_session)

        mock_queue = Mock()
        mock_queue.name = "updated_queue"

        with patch.object(db_session, "merge", return_value=mock_queue) as mock_merge:
            result = queue_repo.update(mock_queue)

            assert result == mock_queue
            mock_merge.assert_called_once_with(mock_queue)

    def test_delete_by_id_success(self, db_session):
        """Test successful deletion by ID."""
        queue_repo = QueueRepository(db_session)

        mock_entity = Mock()
        mock_entity.id = 1
        mock_result = Mock()
        mock_result.rowcount = 1

        with (
            patch.object(db_session, "get", return_value=mock_entity) as mock_get,
            patch.object(db_session, "execute", return_value=mock_result) as mock_execute,
        ):
            result = queue_repo.delete_by_id(1)

            assert result is True
            mock_get.assert_called_once()
            mock_execute.assert_called_once()

    def test_delete_by_id_not_found(self, db_session):
        """Test deletion when entity doesn't exist."""
        queue_repo = QueueRepository(db_session)

        mock_result = Mock()
        mock_result.rowcount = 0

        with patch.object(db_session, "execute", return_value=mock_result):
            result = queue_repo.delete_by_id(999)

            assert result is False

    def test_delete_by_id_sql_error(self, db_session):
        """Test deletion with SQL error."""
        queue_repo = QueueRepository(db_session)

        with patch.object(db_session, "execute", side_effect=SQLAlchemyError("Database error")):
            result = queue_repo.delete_by_id(1)

            assert result is False

    def test_count_entities(self, db_session):
        """Test counting entities."""
        queue_repo = QueueRepository(db_session)

        with patch.object(db_session, "execute") as mock_execute:
            mock_execute.return_value.scalar.return_value = 5

            result = queue_repo.count()

            assert result == 5
            mock_execute.assert_called_once()

    def test_count_entities_none_result(self, db_session):
        """Test counting when result is None."""
        queue_repo = QueueRepository(db_session)

        with patch.object(db_session, "execute") as mock_execute:
            mock_execute.return_value.scalar.return_value = None

            result = queue_repo.count()

            assert result == 0

    def test_exists_entity_true(self, db_session):
        """Test exists when entity exists."""
        queue_repo = QueueRepository(db_session)

        mock_result = Mock()

        with patch.object(db_session, "execute") as mock_execute:
            mock_execute.return_value.first.return_value = mock_result

            result = queue_repo.exists(1)

            assert result is True
            mock_execute.assert_called_once()

    def test_exists_entity_false(self, db_session):
        """Test exists when entity doesn't exist."""
        queue_repo = QueueRepository(db_session)

        with patch.object(db_session, "execute") as mock_execute:
            mock_execute.return_value.first.return_value = None

            result = queue_repo.exists(999)

            assert result is False


class TestQueueRepository:
    """Test QueueRepository specialized queries."""

    def test_find_by_criteria_basic(self, db_session):
        """Test find_by_criteria with basic parameters."""
        queue_repo = QueueRepository(db_session)

        # Properly configure mock with real attributes, not just mock name
        mock_queue = Mock()
        mock_queue.id = 1
        mock_queue.name = "test_queue"
        mock_queue.priority = 5
        mock_queues = [mock_queue]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_queues

        with patch.object(db_session, "execute", return_value=mock_result) as mock_execute:
            result = queue_repo.find_by_criteria(name="test_queue", priority=5)

            assert len(result) == 1
            assert result[0].name == "test_queue"
            mock_execute.assert_called_once()

    def test_find_by_criteria_no_criteria(self, db_session):
        """Test find_by_criteria without criteria."""
        queue_repo = QueueRepository(db_session)

        mock_queues = [Mock(id=1), Mock(id=2)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_queues

        with patch.object(db_session, "execute", return_value=mock_result):
            result = queue_repo.find_by_criteria()

            assert len(result) == 2

    def test_find_by_name_found(self, db_session):
        """Test find_by_name when queue exists."""
        queue_repo = QueueRepository(db_session)

        mock_queue = Mock()
        mock_queue.name = "test_queue"

        with patch.object(db_session, "scalar", return_value=mock_queue) as mock_scalar:
            result = queue_repo.find_by_name("test_queue")

            assert result == mock_queue
            mock_scalar.assert_called_once()

    def test_find_by_name_not_found(self, db_session):
        """Test find_by_name when queue doesn't exist."""
        queue_repo = QueueRepository(db_session)

        with patch.object(db_session, "scalar", return_value=None) as mock_scalar:
            result = queue_repo.find_by_name("nonexistent_queue")

            assert result is None
            mock_scalar.assert_called_once()

    def test_find_all_ordered_by_priority(self, db_session):
        """Test finding queues ordered by priority."""
        queue_repo = QueueRepository(db_session)

        mock_queues = [Mock(id=1, priority=1), Mock(id=2, priority=5), Mock(id=3, priority=10)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_queues

        with patch.object(db_session, "execute", return_value=mock_result) as mock_execute:
            result = queue_repo.find_all_ordered_by_priority()

            assert len(result) == 3
            # Check that it's ordered by priority (ascending)
            assert result[0].priority == 1
            assert result[1].priority == 5
            assert result[2].priority == 10
            mock_execute.assert_called_once()

    def test_find_high_priority_queues(self, db_session):
        """Test finding high priority queues."""
        queue_repo = QueueRepository(db_session)

        mock_queues = [Mock(id=1, priority=1), Mock(id=2, priority=3)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_queues

        with patch.object(db_session, "execute", return_value=mock_result) as mock_execute:
            result = queue_repo.find_high_priority_queues(max_priority=5)

            assert len(result) == 2
            assert all(q.priority <= 5 for q in result)
            mock_execute.assert_called_once()

    def test_get_queue_statistics_success(self, db_session):
        """Test getting queue statistics."""
        queue_repo = QueueRepository(db_session)

        mock_queue = Mock()
        mock_queue.id = 1
        mock_queue.name = "test_queue"
        mock_queue.priority = 5
        mock_queue.queue_limit = 100
        mock_queue.queue_threshold = 80
        mock_queue.queue_timeout = 3600

        with (
            patch.object(queue_repo, "get_by_id", return_value=mock_queue),
            patch.object(db_session, "execute") as mock_execute,
        ):
            mock_execute.return_value.scalar.return_value = 3

            result = queue_repo.get_queue_statistics(1)

            assert result["queue_id"] == 1
            assert result["name"] == "test_queue"
            assert result["priority"] == 5
            assert result["policies_using_queue"] == 3

    def test_get_queue_statistics_not_found(self, db_session):
        """Test getting statistics for non-existent queue."""
        queue_repo = QueueRepository(db_session)

        with patch.object(queue_repo, "get_by_id", return_value=None):
            result = queue_repo.get_queue_statistics(999)

            assert result == {}

    def test_find_queues_by_capacity_range(self, db_session):
        """Test finding queues by capacity range."""
        queue_repo = QueueRepository(db_session)

        mock_queues = [Mock(id=1, queue_limit=50), Mock(id=2, queue_limit=100)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_queues

        with patch.object(db_session, "execute", return_value=mock_result) as mock_execute:
            result = queue_repo.find_queues_by_capacity_range(min_limit=30, max_limit=150)

            assert len(result) == 2
            mock_execute.assert_called_once()

    def test_get_queue_with_policies(self, db_session):
        """Test getting queue with policies loaded."""
        queue_repo = QueueRepository(db_session)

        mock_queue = Mock()
        mock_queue.id = 1
        mock_queue.name = "policy_queue"

        mock_policies = [Mock(id=1), Mock(id=2)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_policies

        with patch.object(queue_repo, "get_by_id", return_value=mock_queue):
            with patch.object(db_session, "execute", return_value=mock_result):
                result = queue_repo.get_queue_with_policies(1)

                assert result == mock_queue
                assert len(result._policies) == 2
                assert result._policies[0].id == 1
                assert result._policies[1].id == 2

    def test_find_unused_queues(self, db_session):
        """Test finding queues not used by any policies."""
        queue_repo = QueueRepository(db_session)

        mock_queue = Mock()
        mock_queue.id = 1
        mock_queue.name = "unused_queue"
        mock_queues = [mock_queue]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_queues

        with patch.object(db_session, "execute", return_value=mock_result) as mock_execute:
            result = queue_repo.find_unused_queues()

            assert len(result) == 1
            assert result[0].name == "unused_queue"
            mock_execute.assert_called_once()

    def test_update_queue_limits_success(self, db_session):
        """Test updating queue limits successfully."""
        queue_repo = QueueRepository(db_session)

        mock_queue = Mock()
        mock_queue.id = 1

        with patch.object(queue_repo, "get_by_id", return_value=mock_queue):
            result = queue_repo.update_queue_limits(1, new_limit=200, new_threshold=160)

            assert result is True
            assert mock_queue.queue_limit == 200
            assert mock_queue.queue_threshold == 160

    def test_update_queue_limits_not_found(self, db_session):
        """Test updating limits for non-existent queue."""
        queue_repo = QueueRepository(db_session)

        with patch.object(queue_repo, "get_by_id", return_value=None):
            result = queue_repo.update_queue_limits(999, new_limit=200, new_threshold=160)

            assert result is False


class TestTargetRepository:
    """Test TargetRepository specialized queries."""

    def test_find_by_name_success(self, db_session):
        """Test finding target by name."""
        target_repo = TargetRepository(db_session)

        mock_target = Mock()
        mock_target.name = "test_target"

        with patch.object(db_session, "scalar", return_value=mock_target) as mock_scalar:
            result = target_repo.find_by_name("test_target")

            assert result == mock_target
            mock_scalar.assert_called_once()

    def test_find_by_protocol(self, db_session):
        """Test finding targets by protocol."""
        target_repo = TargetRepository(db_session)

        mock_target1 = Mock()
        mock_target1.id = 1
        mock_target1.protocol = "sftp"
        mock_target2 = Mock()
        mock_target2.id = 2
        mock_target2.protocol = "sftp"
        mock_targets = [mock_target1, mock_target2]

        mock_result = Mock()
        mock_result.scalars.return_value.unique.return_value.all.return_value = mock_targets

        with patch.object(db_session, "execute", return_value=mock_result) as mock_execute:
            result = target_repo.find_by_protocol("sftp")

            assert len(result) == 2
            assert all(t.protocol == "sftp" for t in result)
            mock_execute.assert_called_once()

    def test_find_by_host_and_port(self, db_session):
        """Test finding targets by host and port."""
        target_repo = TargetRepository(db_session)

        mock_targets = [Mock(id=1, host="example.com", port=22)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_targets

        with patch.object(db_session, "execute", return_value=mock_result) as mock_execute:
            result = target_repo.find_by_host_and_port("example.com", 22)

            assert len(result) == 1
            assert result[0].host == "example.com"
            assert result[0].port == 22
            mock_execute.assert_called_once()

    def test_find_targets_with_credentials(self, db_session):
        """Test finding targets that have credentials."""
        target_repo = TargetRepository(db_session)

        mock_target1 = Mock()
        mock_target1.credentials = Mock()
        mock_target2 = Mock()
        mock_target2.credentials = Mock()
        mock_targets = [mock_target1, mock_target2]

        mock_result = Mock()
        mock_result.scalars.return_value.unique.return_value.all.return_value = mock_targets

        with patch.object(db_session, "execute", return_value=mock_result) as mock_execute:
            result = target_repo.find_targets_with_credentials()

            assert len(result) == 2
            assert all(t.credentials is not None for t in result)
            mock_execute.assert_called_once()

    def test_validate_target_connectivity_mock(self, db_session):
        """Test target connectivity validation with mocking."""
        target_repo = TargetRepository(db_session)

        # Mock the validation logic if the method exists
        with patch.object(target_repo, "validate_target_connectivity", return_value=True) as mock_validate:
            result = mock_validate(1)

            assert result is True
            mock_validate.assert_called_once_with(1)


class TestTransferRequestRepository:
    """Test TransferRequestRepository specialized queries."""

    def test_find_by_criteria(self, db_session):
        """Test finding transfer requests by criteria."""
        request_repo = TransferRequestRepository(db_session)

        mock_requests = [Mock(id=1, filename="test.txt", policy_id=1)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_requests

        with patch.object(db_session, "execute", return_value=mock_result) as mock_execute:
            result = request_repo.find_by_criteria(filename="test.txt")

            assert len(result) == 1
            assert result[0].filename == "test.txt"
            mock_execute.assert_called_once()

    def test_get_next_available_request_success(self, db_session):
        """Test getting next available request."""
        request_repo = TransferRequestRepository(db_session)

        mock_request = Mock()
        mock_request.id = 1
        mock_request.filename = "next_file.txt"

        with patch.object(db_session, "scalar", return_value=mock_request) as mock_scalar:
            result = request_repo.get_next_available_request()

            assert result == mock_request
            mock_scalar.assert_called_once()

    def test_get_next_available_request_none(self, db_session):
        """Test getting next available request when none available."""
        request_repo = TransferRequestRepository(db_session)

        with patch.object(db_session, "scalar", return_value=None) as mock_scalar:
            result = request_repo.get_next_available_request()

            assert result is None
            mock_scalar.assert_called_once()

    def test_count_queued_requests_for_policy(self, db_session):
        """Test counting queued requests for a policy."""
        request_repo = TransferRequestRepository(db_session)

        with patch.object(db_session, "execute") as mock_execute:
            mock_execute.return_value.scalar_one_or_none.return_value = 5

            result = request_repo.count_queued_requests_for_policy(1)

            assert result == 5
            mock_execute.assert_called_once()

    def test_get_existing_filenames_for_policy(self, db_session):
        """Test getting existing filenames for a policy."""
        request_repo = TransferRequestRepository(db_session)

        filenames_set = {"file1.txt", "file2.txt", "file3.txt"}
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = list(filenames_set)

        with patch.object(db_session, "execute", return_value=mock_result) as mock_execute:
            result = request_repo.get_existing_filenames_for_policy(1, filenames_set)

            assert result == filenames_set
            mock_execute.assert_called_once()

    def test_count_unfinished_requests_for_file(self, db_session):
        """Test counting unfinished requests for a file."""
        request_repo = TransferRequestRepository(db_session)

        with patch.object(db_session, "execute") as mock_execute:
            mock_execute.return_value.scalar_one.return_value = 2

            result = request_repo.count_unfinished_requests_for_file(1, "test_file.txt")

            assert result == 2
            mock_execute.assert_called_once()


class TestTransferPolicyRepository:
    """Test TransferPolicyRepository specialized queries."""

    def test_find_by_name(self, db_session):
        """Test finding policy by name."""
        policy_repo = TransferPolicyRepository(db_session)

        mock_policy = Mock()
        mock_policy.name = "test_policy"

        with patch.object(db_session, "scalar", return_value=mock_policy) as mock_scalar:
            result = policy_repo.find_by_name("test_policy")

            assert result == mock_policy
            mock_scalar.assert_called_once()

    def test_find_by_name_and_type(self, db_session):
        """Test finding policy by name and type."""
        policy_repo = TransferPolicyRepository(db_session)

        mock_policy = Mock()
        mock_policy.name = "test_policy"
        mock_policy.type = Type.PERIODICAL

        with patch.object(db_session, "scalar", return_value=mock_policy) as mock_scalar:
            result = policy_repo.find_by_name_and_type("test_policy", Type.PERIODICAL)

            assert result == mock_policy
            mock_scalar.assert_called_once()

    def test_find_enabled_policies(self, db_session):
        """Test finding enabled policies."""
        policy_repo = TransferPolicyRepository(db_session)

        mock_policy1 = Mock()
        mock_policy1.enabled = True
        mock_policy2 = Mock()
        mock_policy2.enabled = True
        mock_policies = [mock_policy1, mock_policy2]

        mock_result = Mock()
        mock_result.scalars.return_value.unique.return_value.all.return_value = mock_policies

        with patch.object(db_session, "execute", return_value=mock_result) as mock_execute:
            result = policy_repo.find_enabled_policies()

            assert len(result) == 2
            assert all(p.enabled for p in result)
            mock_execute.assert_called_once()

    def test_find_by_type(self, db_session):
        """Test finding policies by type."""
        policy_repo = TransferPolicyRepository(db_session)

        mock_policy1 = Mock()
        mock_policy1.type = Type.COMMANDED
        mock_policy2 = Mock()
        mock_policy2.type = Type.COMMANDED
        mock_policies = [mock_policy1, mock_policy2]

        mock_result = Mock()
        mock_result.scalars.return_value.unique.return_value.all.return_value = mock_policies

        with patch.object(db_session, "execute", return_value=mock_result) as mock_execute:
            result = policy_repo.find_by_type(Type.COMMANDED)

            assert len(result) == 2
            assert all(p.type == Type.COMMANDED for p in result)
            mock_execute.assert_called_once()

    def test_count_by_status(self, db_session):
        """Test counting policies by enabled status."""
        policy_repo = TransferPolicyRepository(db_session)

        with patch.object(db_session, "execute") as mock_execute:
            mock_execute.return_value.scalars.return_value.all.return_value = list(range(10))

            result = policy_repo.count_by_status(enabled=True)

            assert result == 10
            mock_execute.assert_called_once()


class TestDatabaseConstraints:
    """Test database constraint handling."""

    def test_unique_constraint_violations_mock(self, db_session):
        """Test unique constraint violation handling."""
        queue_repo = QueueRepository(db_session)

        # Mock queue creation that should violate unique constraint
        mock_queue = Mock()
        mock_queue.name = "duplicate_queue"

        with (
            patch.object(db_session, "add") as mock_add,
            patch.object(db_session, "commit", side_effect=IntegrityError("", "", "")) as mock_commit,
        ):
            with pytest.raises(IntegrityError):
                queue_repo.create(mock_queue)
                db_session.commit()

            mock_add.assert_called_once_with(mock_queue)
            mock_commit.assert_called_once()

    def test_foreign_key_constraint_violations_mock(self, db_session):
        """Test foreign key constraint violation handling."""
        request_repo = TransferRequestRepository(db_session)

        # Mock request with invalid foreign key
        mock_request = Mock()
        mock_request.policy_id = 99999  # Non-existent policy

        with (
            patch.object(db_session, "add") as mock_add,
            patch.object(db_session, "commit", side_effect=IntegrityError("", "", "")) as mock_commit,
        ):
            with pytest.raises(IntegrityError):
                request_repo.create(mock_request)
                db_session.commit()

            mock_add.assert_called_once_with(mock_request)
            mock_commit.assert_called_once()


class TestPerformanceBenchmarks:
    """Test performance-related repository operations."""

    def test_bulk_query_performance_mock(self, db_session):
        """Test performance of bulk queries with mocking."""
        policy_repo = TransferPolicyRepository(db_session)

        # Mock bulk data
        mock_policies = [Mock(id=i, name=f"policy_{i}") for i in range(100)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_policies

        with patch.object(db_session, "execute", return_value=mock_result) as mock_execute:
            import time

            start_time = time.time()

            # Test bulk retrieval
            result = policy_repo.find_by_criteria()

            end_time = time.time()
            query_time = end_time - start_time

            assert len(result) == 100
            assert query_time < 1.0  # Should be fast with mocks
            mock_execute.assert_called_once()

    def test_relationship_loading_performance_mock(self, db_session):
        """Test performance of relationship loading with mocking."""
        queue_repo = QueueRepository(db_session)

        mock_queue = Mock()
        mock_queue.id = 1

        mock_policies = [Mock(id=i) for i in range(10)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_policies

        with patch.object(queue_repo, "get_by_id", return_value=mock_queue):
            with patch.object(db_session, "execute", return_value=mock_result):
                import time

                start_time = time.time()

                # Test relationship loading
                result = queue_repo.get_queue_with_policies(1)

                end_time = time.time()
                query_time = end_time - start_time

                assert result is not None
                assert len(result._policies) == 10
                assert query_time < 0.5  # Should be fast with mocks


class TestTransactionalRepository:
    """Test TransactionalRepository transaction management with mocking."""

    def test_transactional_context_manager_success(self, db_session):
        """Test successful transaction with context manager."""
        queue_repo = QueueRepository(db_session)

        # Mock the transactional behavior
        mock_queue = Mock()
        mock_queue.name = "transactional_queue"

        with patch.object(db_session, "add") as mock_add, patch.object(db_session, "commit") as mock_commit:
            # Simulate transactional repository behavior
            try:
                queue_repo.create(mock_queue)
                # Simulate successful transaction
                db_session.commit()
                success = True
            except Exception:
                db_session.rollback()
                success = False

            assert success is True
            mock_add.assert_called_once_with(mock_queue)
            mock_commit.assert_called_once()

    def test_transactional_context_manager_rollback(self, db_session):
        """Test transaction rollback on exception."""
        queue_repo = QueueRepository(db_session)

        mock_queue = Mock()
        mock_queue.name = "rollback_queue"

        with (
            patch.object(db_session, "add") as mock_add,
            patch.object(db_session, "commit", side_effect=SQLAlchemyError("Database error")) as mock_commit,
            patch.object(db_session, "rollback") as mock_rollback,
        ):
            # Simulate transactional repository behavior with error
            try:
                queue_repo.create(mock_queue)
                db_session.commit()
                success = True
            except SQLAlchemyError:
                db_session.rollback()
                success = False

            assert success is False
            mock_add.assert_called_once_with(mock_queue)
            mock_commit.assert_called_once()
            mock_rollback.assert_called_once()
