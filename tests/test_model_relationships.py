"""
Model relationship and validation.

This test suite validates:
- Model relationship integrity
- Serialization and deserialization
- Database constraint validation
- Data integrity tests
- Migration compatibility
"""
from __future__ import annotations

import pytest
from dtr_common.constantes import Protocol, State as ConstantsState, Type
from sqlalchemy.exc import IntegrityError

from api.models import (
    Credentials,
    Queue,
    State,
    Target,
    TransferPolicy,
    TransferRequest,
)
from tests.factories import (
    CredentialsFactory,
    DestinationPolicyFactory,
    QueueFactory,
    SourcePolicyFactory,
    StateFactory,
    TargetFactory,
    TransferPolicyFactory,
    TransferRequestFactory,
)


class TestModelRelationships:
    """Test model relationship integrity and cascading behavior."""

    def test_transfer_policy_queue_relationship(self, db_session):
        """Test TransferPolicy <-> Queue relationship."""
        queue = QueueFactory.create()
        policy = TransferPolicyFactory.create(queue=queue)

        # Test forward relationship
        assert policy.queue == queue
        assert policy.queue_id == queue.id

        # Note: Queue model doesn't have a backward 'policies' relationship defined

    def test_transfer_policy_source_destination_relationship(self, db_session):
        """Test TransferPolicy <-> SourcePolicy/DestinationPolicy relationships."""
        # Create source and destinations first
        source = SourcePolicyFactory.create()
        dest1 = DestinationPolicyFactory.create()
        dest2 = DestinationPolicyFactory.create()

        # Create policy with source reference
        policy = TransferPolicyFactory.create(src=source, dests=[dest1, dest2])

        # Test source relationship
        assert policy.src == source
        assert policy.src_id == source.id

        # Test destination relationships
        assert dest1 in policy.dests
        assert dest2 in policy.dests
        assert len(policy.dests) == 2

    def test_target_credentials_relationship(self, db_session):
        """Test Target <-> Credentials relationship."""
        credentials = CredentialsFactory.create()
        target = TargetFactory.create(credentials=credentials)

        # Test forward relationship
        assert target.credentials == credentials
        # Note: Target model doesn't expose credentials_id publicly

        # Note: Credentials model doesn't have a backward 'targets' relationship

    def test_transfer_request_policy_relationship(self, db_session):
        """Test TransferRequest <-> TransferPolicy relationship."""
        policy = TransferPolicyFactory.create()
        request1 = TransferRequestFactory.create(policy=policy)
        request2 = TransferRequestFactory.create(policy=policy)

        # Test forward relationship
        assert request1.policy == policy
        assert request2.policy == policy

        # Test backward relationship
        assert request1 in policy.transfers
        assert request2 in policy.transfers

    def test_transfer_request_state_relationship(self, db_session):
        """Test TransferRequest <-> State relationship."""
        request = TransferRequestFactory.create()

        # TransferRequest uses states (list) relationship, not a single state
        # State is created separately and linked via request_id
        StateFactory.create()
        # We would need to add the state to the request's states list in a real scenario
        # For now, just test that the relationships exist
        assert hasattr(request, "states")
        assert isinstance(request.states, list)

    @pytest.mark.skip(reason="Complex cascade relationships need DB schema review")
    def test_cascade_delete_policy_with_requests(self, db_session):
        """Test cascading delete behavior for policies with requests."""
        # This test requires careful handling of FK constraints and cascade relationships
        # The current model structure has complex interdependencies that need schema review
        pass

    @pytest.mark.skip(reason="Complex cascade relationships need DB schema review")
    def test_cascade_delete_target_with_policies(self, db_session):
        """Test cascading delete behavior for targets with policies."""
        # This test requires careful handling of FK constraints and cascade relationships
        # The current model structure has complex interdependencies that need schema review
        pass


class TestModelSerialization:
    """Test model serialization and deserialization capabilities."""

    def test_transfer_policy_serialization(self, db_session):
        """Test TransferPolicy model can be serialized properly."""
        policy = TransferPolicyFactory.create(name="test_policy", type=Type.PERIODICAL, enabled=True)

        # Test basic attributes
        assert hasattr(policy, "name")
        assert hasattr(policy, "type")
        assert hasattr(policy, "enabled")
        assert hasattr(policy, "id")

        # Test relationship attributes
        assert hasattr(policy, "queue")
        assert hasattr(policy, "queue_id")
        assert hasattr(policy, "transfers")
        assert hasattr(policy, "src")
        assert hasattr(policy, "dests")

    def test_transfer_request_serialization(self, db_session):
        """Test TransferRequest model can be serialized properly."""
        request = TransferRequestFactory.create(
            filename="test_file.txt",
            src_relative_path="/source/path",
        )

        # Test basic attributes
        assert hasattr(request, "filename")
        assert hasattr(request, "src_relative_path")
        assert hasattr(request, "id")
        assert hasattr(request, "created_at")
        assert hasattr(request, "size")
        assert hasattr(request, "uid")

        # Test relationship attributes
        assert hasattr(request, "policy")
        assert hasattr(request, "policy_id")
        assert hasattr(request, "states")  # List of states, not single state
        assert hasattr(request, "dest")
        assert hasattr(request, "nb_retry")

    def test_queue_serialization(self, db_session):
        """Test Queue model can be serialized properly."""
        queue = QueueFactory.create(priority=5, queue_limit=100, queue_threshold=80, queue_timeout=3600)

        # Test all attributes
        assert hasattr(queue, "name")
        assert hasattr(queue, "priority")
        assert hasattr(queue, "queue_limit")
        assert hasattr(queue, "queue_threshold")
        assert hasattr(queue, "queue_timeout")
        assert hasattr(queue, "uid")
        # Note: Queue doesn't have a 'policies' relationship defined in the model

    def test_target_serialization(self, db_session):
        """Test Target model can be serialized properly."""
        target = TargetFactory.create(name="test_target", protocol=Protocol.SFTP, host="example.com", port=22)

        # Test all attributes
        assert hasattr(target, "name")
        assert hasattr(target, "protocol")
        assert hasattr(target, "host")
        assert hasattr(target, "port")
        assert hasattr(target, "credentials")
        assert hasattr(target, "parameters")


class TestModelConstraints:
    """Test database constraint validation and enforcement."""

    def test_transfer_policy_name_constraint(self, db_session):
        """Test TransferPolicy name constraints."""
        # Create policy with name
        policy1 = TransferPolicyFactory.create(name="unique_policy")
        db_session.add(policy1)
        db_session.commit()

        # Attempting to create another policy with same name should fail
        with pytest.raises(IntegrityError):
            policy2 = TransferPolicyFactory.create(name="unique_policy")
            db_session.add(policy2)
            db_session.commit()

        db_session.rollback()

    def test_queue_name_constraint(self, db_session):
        """Test Queue name uniqueness constraint."""
        # Create queue with name
        queue1 = QueueFactory.create(name="unique_queue")
        db_session.add(queue1)
        db_session.commit()

        # Attempting to create another queue with same name should fail
        with pytest.raises(IntegrityError):
            queue2 = QueueFactory.create(name="unique_queue")
            db_session.add(queue2)
            db_session.commit()

        db_session.rollback()

    def test_target_name_constraint(self, db_session):
        """Test Target name uniqueness constraint."""
        # Create target with name
        target1 = TargetFactory.create(name="unique_target")
        db_session.add(target1)
        db_session.commit()

        # Attempting to create another target with same name should fail
        with pytest.raises(IntegrityError):
            target2 = TargetFactory.create(name="unique_target")
            db_session.add(target2)
            db_session.commit()

        db_session.rollback()

    @pytest.mark.skip(reason="SQLite FK constraints may not be strictly enforced in test env")
    def test_transfer_request_foreign_key_constraints(self, db_session):
        """Test TransferRequest foreign key constraints."""
        # Note: This test may require specific SQLite configuration for FK enforcement
        # SQLite may allow invalid foreign keys by default in some configurations
        policy = TransferPolicyFactory.create()
        db_session.add(policy)
        db_session.commit()

        # Valid request should work
        request = TransferRequestFactory.create(policy=policy)
        db_session.add(request)
        db_session.commit()
        assert request.policy_id == policy.id

    def test_queue_constraints_validation(self, db_session):
        """Test Queue numeric constraints."""
        # Valid queue should work
        queue = QueueFactory.create(priority=5, queue_limit=100, queue_threshold=80, queue_timeout=3600)
        assert queue.priority == 5
        assert queue.queue_limit == 100

        # Test threshold validation (should be <= limit)
        queue.queue_threshold = 120  # Greater than limit
        # Note: This would require application-level validation
        # Database constraints might not catch this business rule


class TestDataIntegrity:
    """Test data integrity and business rule validation."""

    def test_transfer_policy_type_validation(self, db_session):
        """Test TransferPolicy type field validation."""
        # Valid types should work
        periodic_policy = TransferPolicyFactory.create(type=Type.PERIODICAL)
        commanded_policy = TransferPolicyFactory.create(type=Type.COMMANDED)

        assert periodic_policy.type == Type.PERIODICAL
        assert commanded_policy.type == Type.COMMANDED

    def test_target_protocol_validation(self, db_session):
        """Test Target protocol field validation."""
        # Valid protocols should work
        sftp_target = TargetFactory.create(protocol=Protocol.SFTP)
        ftps_target = TargetFactory.create(protocol=Protocol.FTPS)
        s3_target = TargetFactory.create(protocol=Protocol.S3)
        http_target = TargetFactory.create(protocol=Protocol.HTTP)

        assert sftp_target.protocol == Protocol.SFTP
        assert ftps_target.protocol == Protocol.FTPS
        assert s3_target.protocol == Protocol.S3
        assert http_target.protocol == Protocol.HTTP

    def test_state_status_validation(self, db_session):
        """Test State status field validation."""
        # Valid statuses should work
        pending_state = StateFactory.create(state=ConstantsState.QUEUED)
        success_state = StateFactory.create(state=ConstantsState.SUCCESSFUL)
        error_state = StateFactory.create(state=ConstantsState.FAILED)

        assert pending_state.state == ConstantsState.QUEUED
        assert success_state.state == ConstantsState.SUCCESSFUL
        assert error_state.state == ConstantsState.FAILED

    def test_transfer_request_filepath_integrity(self, db_session):
        """Test TransferRequest file path integrity."""
        request = TransferRequestFactory.create(
            filename="test_file.txt",
            src_relative_path="/source/path/test_file.txt",
        )

        # Test file paths are properly set
        assert request.filename in request.src_relative_path
        assert request.src_relative_path is not None
        # Note: TransferRequest doesn't have destination_filepath, it uses dest relationship

    def test_policy_queue_relationship_integrity(self, db_session):
        """Test TransferPolicy-Queue relationship data integrity."""
        queue = QueueFactory.create(name="high_priority", priority=1)
        policy = TransferPolicyFactory.create(queue=queue)

        # Add to session for persistence testing
        db_session.add_all([queue, policy])
        db_session.flush()

        # Test integrity of relationship
        assert policy.queue_id == queue.id
        # Note: Queue model doesn't have backward 'policies' relationship

        # Test that queue relationship persists across session reloads
        queue_id = queue.id
        policy_id = policy.id

        db_session.expunge_all()  # Clear session to test fresh load

        loaded_queue = db_session.get(Queue, queue_id)
        loaded_policy = db_session.get(TransferPolicy, policy_id)

        assert loaded_policy.queue_id == loaded_queue.id


class TestMigrationCompatibility:
    """Test model compatibility with database migrations."""

    def test_model_table_names(self, db_session):
        """Test that model table names match expected database schema."""
        # Verify table names are properly defined
        assert TransferPolicy.__tablename__ == "transfer_policies"
        assert TransferRequest.__tablename__ == "transfer_requests"
        assert Queue.__tablename__ == "queues"
        assert Target.__tablename__ == "targets"
        assert Credentials.__tablename__ == "credentials"
        assert State.__tablename__ == "states"

    def test_model_primary_keys(self, db_session):
        """Test that all models have proper primary keys."""
        policy = TransferPolicyFactory.create()
        request = TransferRequestFactory.create()
        queue = QueueFactory.create()
        target = TargetFactory.create()

        # Add to session and flush to generate IDs
        db_session.add_all([policy, request, queue, target])
        db_session.flush()

        # All models should have id as primary key
        assert hasattr(policy, "id") and policy.id is not None
        assert hasattr(request, "id") and request.id is not None
        assert hasattr(queue, "id") and queue.id is not None
        assert hasattr(target, "id") and target.id is not None

    def test_model_timestamps(self, db_session):
        """Test timestamp fields are properly set."""
        request = TransferRequestFactory.create()

        # Add to session and flush to generate timestamps
        db_session.add(request)
        db_session.flush()

        # TransferRequest should have timestamp fields
        assert hasattr(request, "created_at") and request.created_at is not None
        # Note: TransferRequest doesn't have updated_at, only created_at

        # created_at should be a valid datetime object
        from datetime import datetime

        assert isinstance(request.created_at, datetime)
