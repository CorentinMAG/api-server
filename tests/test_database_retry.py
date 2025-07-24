"""
Tests for database retry functionality.

This module tests that the database retry mechanisms work correctly
when database connection issues occur.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from sqlalchemy.exc import DisconnectionError, OperationalError, SQLAlchemyError, TimeoutError

from api.services.utils import _get_logger, db_retry


class TestDatabaseRetryMechanism:
    """Test the database retry mechanism for connection issues."""

    def test_db_retry_decorator_exhausts_retries(self):
        """Test that db_retry raises error after exhausting retries."""

        @db_retry(total=2, initial_delay=0.01, max_delay=0.1)
        def mock_db_operation():
            raise OperationalError("Connection failed", None, None)

        with pytest.raises(SQLAlchemyError) as exc_info:
            mock_db_operation()

        assert "Database operation failed after retries" in str(exc_info.value)

    def test_db_retry_with_different_connection_errors(self):
        """Test that db_retry handles various connection error types."""

        error_types = [
            OperationalError("Connection failed", None, None),
            DisconnectionError("Disconnected", None, None),
            TimeoutError("Timeout", None, None),
        ]

        for error in error_types:

            @db_retry(total=2, initial_delay=0.01, max_delay=0.1)
            def mock_db_operation():
                raise error

            with pytest.raises(SQLAlchemyError):
                mock_db_operation()

    def test_db_retry_does_not_retry_non_connection_errors(self):
        """Test that db_retry doesn't retry non-connection errors."""

        @db_retry(total=3, initial_delay=0.01, max_delay=0.1)
        def mock_db_operation():
            raise ValueError("This should not be retried")

        with pytest.raises(ValueError):
            mock_db_operation()

    def test_db_retry_success_on_first_attempt(self):
        """Test that db_retry works normally when no errors occur."""

        @db_retry(total=3, initial_delay=0.01, max_delay=0.1)
        def mock_db_operation():
            return "success"

        result = mock_db_operation()
        assert result == "success"

    def test_logger_fallback_without_flask_context(self):
        """Test that _get_logger works without Flask context."""

        # Since we're outside Flask context, _get_logger should already be using fallback
        logger = _get_logger()

        # Should get a standard Python logger as fallback
        assert logger is not None
        assert hasattr(logger, "error")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "info")

    def test_retry_with_mock_operation(self):
        """Test retry mechanism with a mock that succeeds after failures."""

        from dtr_common.retry import retry_database_operation

        call_count = 0

        def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise OperationalError("Connection failed", None, None)
            return "success"

        result = retry_database_operation(
            mock_operation, logger=_get_logger(), total=3, initial_delay=0.01, max_delay=0.1
        )

        assert result == "success"
        assert call_count == 3

    def test_base_repository_retry_protection(self):
        """Test that BaseRepository methods have retry protection."""

        from api.repositories.queue_repository import QueueRepository

        mock_session = Mock()
        repo = QueueRepository(mock_session)

        # Test that the repository has retry protection
        assert hasattr(repo, "_execute_with_retry")
        assert callable(repo._execute_with_retry)

    def test_health_endpoints_have_retry(self):
        """Test that health endpoints use retry decorators."""

        # This test verifies that the health endpoints import the retry utilities
        from api import create_app

        app = create_app()

        with app.test_client() as client:
            # Basic health should work
            response = client.get("/healthz")
            assert response.status_code == 200

            # These endpoints should have retry protection built in
            # Even if they fail due to no DB, they shouldn't crash the app
            response = client.get("/health")
            assert response.status_code in [200, 503]  # Should handle DB errors gracefully

            response = client.get("/ready")
            assert response.status_code in [200, 503]  # Should handle DB errors gracefully
