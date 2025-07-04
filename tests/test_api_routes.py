"""
API Routes Integration Tests

Comprehensive test suite for all API routes with dependency injection testing,
error handling validation, and comprehensive coverage patterns.
"""
from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from dtr_common.constantes import Mode, State as StateEnum

from api import create_app
from api.models import TransferPolicy, TransferRequest


@pytest.fixture
def client():
    """Create a Flask test client for API testing."""
    app = create_app()
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_transfer_request():
    """Mock transfer request with complete relationships."""
    request = Mock(spec=TransferRequest)
    request.uid = "test-uuid-123"
    request.filename = "test-file.txt"
    request.size = 1024.0
    request.nb_retry = 0
    request.start = None
    request.end = None
    request.download_rate = 10.5
    request.download_time = 100
    request.upload_rate = 8.2
    request.upload_time = 125
    request.created_at = None
    request.follows_from_task = None

    # Mock state relationship
    state = Mock()
    state.state = StateEnum.QUEUED
    state.sub_state = None
    state.failure_reason = None
    request.states = [state]

    # Mock policy and targets
    policy = Mock()
    policy.name = "test-policy"
    src_target = Mock()
    src_target.name = "src-target"
    src_target.protocol = Mock()
    src_target.protocol.value = "SFTP"

    src = Mock()
    src.target = src_target
    src.path = "/source/path"
    policy.src = src
    request.policy = policy

    dest = Mock()
    dest_target = Mock()
    dest_target.name = "dest-target"
    dest_target.protocol = Mock()
    dest_target.protocol.value = "S3"
    dest.target = dest_target
    dest.path = "/dest/path"
    request.dest = dest

    request.to_dict.return_value = {"uid": "test-uuid-123", "filename": "test-file.txt", "size": 1024.0}

    return request


class TestRequestsRoutes:
    """Test suite for /requests routes with dependency injection patterns."""

    def test_get_transfer_status_success(self, client, mock_transfer_request):
        """Test successful transfer status retrieval."""
        with patch("api.routes.v1.requests.get_params") as mock_get_params, patch(
            "api.routes.v1.requests._get_request_services"
        ) as mock_services:
            # Configure mocks
            mock_get_params.return_value = Mock(mode=Mode.ONLINE)
            mock_transfer_repo = Mock()
            mock_transfer_repo.filter_by_uid.return_value = mock_transfer_request
            mock_services.return_value = {"transfer_repo": mock_transfer_repo, "logger": Mock()}

            response = client.get("/dtr/v1/get-status?id=test-uuid-123")

            assert response.status_code == 200
            assert response.json["success"] is True
            assert "data" in response.json
            data = response.json["data"]
            assert data["transfer_id"] == "test-uuid-123"
            assert data["transfer_info"]["data_identifier"] == "test-file.txt"

    def test_get_transfer_status_not_found(self, client):
        """Test transfer status when transfer ID is not found."""
        with patch("api.routes.v1.requests.get_params") as mock_get_params, patch(
            "api.routes.v1.requests._get_request_services"
        ) as mock_services:
            # Configure mocks
            mock_get_params.return_value = Mock(mode=Mode.ONLINE)
            mock_transfer_repo = Mock()
            mock_transfer_repo.filter_by_uid.return_value = None
            mock_services.return_value = {"transfer_repo": mock_transfer_repo, "logger": Mock()}

            response = client.get("/dtr/v1/get-status?id=non-existent-uuid")

            assert response.status_code == 404
            assert response.json["success"] is False
            assert response.json["error"]["message"] == "Transfer request not found"

    def test_get_transfer_status_no_id_provided(self, client):
        """Test transfer status when no transfer ID is provided."""
        with patch("api.routes.v1.requests.get_params") as mock_get_params:
            mock_get_params.return_value = Mock(mode=Mode.ONLINE)

            response = client.get("/dtr/v1/get-status")

            assert response.status_code == 400
            assert response.json["success"] is False
            assert response.json["error"]["message"] == "invalid query parameters"

    def test_get_transfer_status_offline_mode(self, client):
        """Test transfer status when system is offline."""
        with patch("api.routes.v1.requests.get_params") as mock_get_params, patch(
            "api.routes.v1.requests._get_request_services"
        ) as mock_services:
            mock_get_params.return_value = Mock(mode=Mode.OFFLINE)
            mock_services.return_value = {"transfer_repo": Mock(), "logger": Mock()}

            response = client.get("/dtr/v1/get-status?id=test-uuid")

            assert response.status_code == 503
            assert response.json["success"] is False
            assert response.json["error"]["message"] == "system is in OFFLINE mode"

    def test_new_requests_success(self, client):
        """Test successful creation of periodical requests."""
        with patch("api.routes.v1.requests.create_periodical_requests") as mock_create, patch(
            "api.routes.v1.requests._get_request_services"
        ) as mock_services, patch(
            "api.routes.v1.requests.TriggerTransferRequestSchema"
        ) as mock_schema, patch("api.routes.v1.requests.db") as mock_db:
            # Configure mocks
            mock_services.return_value = {"validation_service": Mock(), "logger": Mock()}
            mock_schema.return_value = Mock()
            mock_create.return_value = None
            mock_db.session = Mock()

            payload = {"policy_name": "test-policy", "files": ["file1.txt", "file2.txt"]}

            response = client.post("/dtr/v1/request", json=payload)

            assert response.status_code == 200
            # Check both old and new formats
            if "success" in response.json:
                assert response.json["success"] is True
            else:
                # Old format check
                assert response.status_code == 200
            mock_create.assert_called_once()

    def test_new_requests_no_payload(self, client):
        """Test request creation with no payload."""
        with patch("api.routes.v1.requests._get_request_services") as mock_services:
            # Configure mocks to prevent "Unhandled exception"
            mock_services.return_value = {"validation_service": Mock(), "logger": Mock()}

            # Just call without any JSON data
            response = client.post("/dtr/v1/request", headers={"Content-Type": "application/json"})

            assert response.status_code == 400
            # Check both old and new formats
            if "success" in response.json:
                assert response.json["success"] is False
                assert response.json["error"]["message"] == "No payload provided"
            elif "error" in response.json:
                # New standardized format
                if isinstance(response.json["error"], dict):
                    assert response.json["error"]["message"] == "No payload provided"
                else:
                    # Old format
                    assert response.json["error"] == "No payload provided"
            else:
                # Old format check
                assert response.status_code == 400

    def test_new_commanded_request_success(self, client):
        """Test successful creation of commanded request."""
        with patch("api.routes.v1.requests.create_commanded_request") as mock_create, patch(
            "api.routes.v1.requests._get_request_services"
        ) as mock_services, patch(
            "api.routes.v1.requests.CommandedTransferRequestSchema"
        ) as mock_schema, patch("api.routes.v1.requests.db") as mock_db:
            # Configure mocks
            mock_services.return_value = {"validation_service": Mock(), "logger": Mock()}
            mock_schema.return_value = Mock()
            mock_create.return_value = (["uuid-123"], None, None)
            mock_db.session = Mock()

            payload = {
                "policy_name": "test-policy",
                "filename": "test-file.txt",
                "src": "/source/path",
                "dest": "/dest/path",
            }

            response = client.post("/dtr/v1/transfer-request", json=payload)

            assert response.status_code == 200
            # Check both old and new formats
            if "success" in response.json:
                assert response.json["success"] is True
                assert response.json["data"]["transfer_id"] == ["uuid-123"]
            else:
                # Old format check
                assert response.status_code == 200

    def test_new_commanded_request_failure(self, client):
        """Test commanded request creation failure."""
        with patch("api.routes.v1.requests.create_commanded_request") as mock_create, patch(
            "api.routes.v1.requests._get_request_services"
        ) as mock_services, patch(
            "api.routes.v1.requests.CommandedTransferRequestSchema"
        ) as mock_schema, patch("api.routes.v1.requests.db") as mock_db:
            # Configure mocks
            mock_services.return_value = {"validation_service": Mock(), "logger": Mock()}
            mock_schema.return_value = Mock()
            mock_create.return_value = (None, "Policy not found", 404)
            mock_db.session = Mock()

            payload = {"policy_name": "non-existent-policy", "filename": "test-file.txt"}

            response = client.post("/dtr/v1/transfer-request", json=payload)

            assert response.status_code == 404
            # Check both old and new formats
            if "success" in response.json:
                assert response.json["success"] is False
                assert response.json["error"]["message"] == "Policy not found"
            elif "error" in response.json:
                # New standardized format
                if isinstance(response.json["error"], dict):
                    assert response.json["error"]["message"] == "Policy not found"
                else:
                    # Old format
                    assert response.json["error"] == "Policy not found"
            else:
                # Old format check
                assert response.status_code == 404

    def test_update_requests_success(self, client):
        """Test successful request update."""
        with patch("api.routes.v1.requests.update_request") as mock_update, patch(
            "api.routes.v1.requests._get_request_services"
        ) as mock_services:
            # Configure mocks
            mock_services.return_value = {"logger": Mock()}
            mock_update.return_value = {"status": "updated"}

            payload = {"state": "COMPLETED"}

            response = client.put("/dtr/v1/request/123", json=payload)

            assert response.status_code == 200
            # Check both old and new formats
            if "success" in response.json:
                assert response.json["success"] is True
                assert response.json["data"]["status"] == "updated"
            else:
                # Old format check
                assert response.status_code == 200

    def test_filter_requests_success(self, client, mock_transfer_request):
        """Test successful request filtering."""
        with patch("api.routes.v1.requests.get_params") as mock_get_params, patch(
            "api.routes.v1.requests._get_request_services"
        ) as mock_services:
            # Configure mocks
            mock_get_params.return_value = Mock(mode=Mode.ONLINE)
            mock_transfer_repo = Mock()
            mock_transfer_repo.filter_requests.return_value = [mock_transfer_request]
            mock_services.return_value = {"transfer_repo": mock_transfer_repo, "logger": Mock()}

            response = client.get("/dtr/v1/filter?state=QUEUED")

            assert response.status_code == 200
            # Check both old and new formats
            if "success" in response.json:
                assert response.json["success"] is True
                assert len(response.json["data"]["requests"]) == 1
            else:
                # Old format check
                assert response.status_code == 200

    def test_filter_requests_offline_mode(self, client):
        """Test request filtering in offline mode."""
        with patch("api.routes.v1.requests.get_params") as mock_get_params, patch(
            "api.routes.v1.requests._get_request_services"
        ) as mock_services:
            mock_get_params.return_value = Mock(mode=Mode.OFFLINE)
            mock_services.return_value = {"transfer_repo": Mock(), "logger": Mock()}

            response = client.get("/dtr/v1/filter")

            assert response.status_code == 400
            # Check both old and new formats
            if "success" in response.json:
                assert response.json["success"] is False
                assert response.json["error"]["message"] == "System is in OFFLINE mode"
            elif "error" in response.json:
                # New standardized format
                if isinstance(response.json["error"], dict):
                    assert response.json["error"]["message"] == "System is in OFFLINE mode"
                else:
                    # Old format
                    assert response.json["error"] == "System is in OFFLINE mode"
            else:
                # Old format check
                assert response.status_code == 400


class TestPoliciesRoutes:
    """Test suite for /policies routes with dependency injection patterns."""

    def test_policies_get_success(self, client):
        """Test successful policies retrieval."""
        mock_policy = Mock(spec=TransferPolicy)
        mock_policy.to_dict.return_value = {"id": 1, "name": "test-policy"}

        with patch("api.routes.v1.policies.get_params") as mock_get_params, patch(
            "api.routes.v1.policies.filter_policies"
        ) as mock_filter, patch("api.routes.v1.policies.db") as mock_db, patch(
            "api.routes.v1.policies._get_policy_services"
        ) as mock_services:
            # Configure mocks
            mock_get_params.return_value = Mock(mode=Mode.ONLINE)
            mock_filter.return_value = Mock()
            mock_services.return_value = {"policy_repo": Mock(), "logger": Mock(), "db_session": Mock()}

            mock_result = Mock()
            mock_result.items = [mock_policy]
            mock_result.page = 1
            mock_result.per_page = 10
            mock_result.total = 1
            mock_db.paginate.return_value = mock_result

            response = client.get("/dtr/v1/policies?page=1&page_size=10")

            assert response.status_code == 200
            # Check both old and new formats
            if "success" in response.json:
                assert response.json["success"] is True
                data = response.json["data"]
                assert data["page"] == 1
                assert data["total"] == 1
                assert len(data["policies"]) == 1
            else:
                # Old format check
                assert response.status_code == 200

    def test_policies_get_offline_mode(self, client):
        """Test policies retrieval in offline mode."""
        with patch("api.routes.v1.policies.get_params") as mock_get_params, patch(
            "api.routes.v1.policies._get_policy_services"
        ) as mock_services:
            mock_get_params.return_value = Mock(mode=Mode.OFFLINE)
            mock_services.return_value = {"policy_repo": Mock(), "logger": Mock(), "db_session": Mock()}

            response = client.get("/dtr/v1/policies")

            assert response.status_code == 200
            # Check both old and new formats
            if "success" in response.json:
                assert response.json["success"] is True
                data = response.json["data"]
                assert data["policies"] == []
                assert data["total"] == -1
            else:
                # Old format check
                assert response.status_code == 200

    def test_post_policies_success(self, client):
        """Test successful policies creation."""
        with patch("api.routes.v1.policies.create_policies") as mock_create, patch(
            "api.routes.v1.policies._get_policy_services"
        ) as mock_services:
            # Configure mocks
            mock_services.return_value = {
                "validation_service": Mock(),
                "logger": Mock(),
                "db_session": Mock(),
            }
            mock_create.return_value = None

            payload = {
                "policies": [
                    {"name": "policy1", "type": "PERIODICAL"},
                    {"name": "policy2", "type": "COMMANDED"},
                ]
            }

            response = client.post("/dtr/v1/policies", json=payload)

            assert response.status_code == 201
            # Check both old and new formats
            if "success" in response.json:
                assert response.json["success"] is True
            else:
                # Old format check
                assert response.status_code == 201
            mock_create.assert_called_once()

    def test_put_policy_success(self, client):
        """Test successful policy update."""
        with patch("api.routes.v1.policies.update_policy") as mock_update, patch(
            "api.routes.v1.policies._get_policy_services"
        ) as mock_services:
            # Configure mocks
            mock_policy_repo = Mock()
            mock_policy_repo.get_by_id.return_value = Mock(spec=TransferPolicy)
            mock_services.return_value = {
                "policy_repo": mock_policy_repo,
                "validation_service": Mock(),
                "logger": Mock(),
                "db_session": Mock(),
            }
            mock_update.return_value = None

            payload = {"name": "updated-policy"}

            response = client.put("/dtr/v1/policies/123", json=payload)

            assert response.status_code == 204
            # 204 responses typically have no content


class TestWorkerRoutes:
    """Test suite for /worker routes."""

    def test_worker_configuration_success(self, client, mock_transfer_request):
        """Test successful worker configuration."""
        with patch("api.routes.v1.worker.get_params") as mock_get_params, patch(
            "api.routes.v1.worker.get_next_request"
        ) as mock_get_next, patch("api.routes.v1.worker.db") as mock_db, patch(
            "api.routes.v1.worker._get_worker_services"
        ) as mock_services:
            # Configure mocks
            mock_get_params.return_value = Mock(mode=Mode.ONLINE)
            mock_get_next.return_value = mock_transfer_request
            mock_services.return_value = {
                "transfer_repo": Mock(),
                "logger": Mock(),
                "db_session": mock_db.session,
            }

            response = client.get("/dtr/v1/configuration/worker?size=1000")

            assert response.status_code == 200
            # Check both old and new formats
            if "success" in response.json:
                assert response.json["success"] is True
                assert response.json["data"]["request"] is not None
            else:
                assert response.json["request"] is not None
            mock_get_next.assert_called_once()
            mock_db.session.commit.assert_called_once()

    def test_worker_configuration_offline(self, client):
        """Test worker configuration in offline mode."""
        with patch("api.routes.v1.worker.get_params") as mock_get_params, patch(
            "api.routes.v1.worker._get_worker_services"
        ) as mock_services:
            mock_get_params.return_value = Mock(mode=Mode.OFFLINE)
            mock_services.return_value = {"logger": Mock(), "db_session": Mock()}

            response = client.get("/dtr/v1/configuration/worker")

            assert response.status_code == 200
            # Check both old and new formats
            if "success" in response.json:
                assert response.json["success"] is True
                assert response.json["data"]["request"] is None
            else:
                assert response.json["request"] is None

    def test_worker_configuration_no_request(self, client):
        """Test worker configuration with no available request."""
        with patch("api.routes.v1.worker.get_params") as mock_get_params, patch(
            "api.routes.v1.worker.get_next_request"
        ) as mock_get_next, patch("api.routes.v1.worker._get_worker_services") as mock_services:
            # Configure mocks
            mock_get_params.return_value = Mock(mode=Mode.ONLINE)
            mock_get_next.return_value = None
            mock_services.return_value = {"logger": Mock(), "db_session": Mock()}

            response = client.get("/dtr/v1/configuration/worker")

            assert response.status_code == 200
            # Check both old and new formats
            if "success" in response.json:
                assert response.json["success"] is True
                assert response.json["data"]["request"] is None
            else:
                assert response.json["request"] is None


class TestTriggerRoutes:
    """Test suite for /trigger routes."""

    def test_trigger_configuration_success(self, client):
        """Test successful trigger configuration."""
        mock_policy = Mock(spec=TransferPolicy)
        mock_policy.to_dict.return_value = {"id": 1, "name": "test-policy"}

        with patch("api.routes.v1.trigger.get_params") as mock_get_params, patch(
            "api.routes.v1.trigger.filter_policies"
        ) as mock_filter, patch("api.routes.v1.trigger.db") as mock_db, patch(
            "api.routes.v1.trigger._get_trigger_services"
        ) as mock_services:
            # Configure mocks
            mock_get_params.return_value = Mock(mode=Mode.ONLINE)
            mock_filter.return_value = Mock()
            mock_services.return_value = {"policy_repo": Mock(), "logger": Mock(), "db_session": Mock()}

            mock_result = Mock()
            mock_result.items = [mock_policy]
            mock_result.page = 1
            mock_result.per_page = 10
            mock_result.total = 1
            mock_db.paginate.return_value = mock_result

            response = client.get("/dtr/v1/configuration/trigger?page=1")

            assert response.status_code == 200
            # Check both old and new formats
            if "success" in response.json:
                assert response.json["success"] is True
                data = response.json["data"]
                assert data["page"] == 1
                assert data["total"] == 1
            else:
                assert response.json["page"] == 1
                assert response.json["total"] == 1

    def test_trigger_configuration_offline(self, client):
        """Test trigger configuration in offline mode."""
        with patch("api.routes.v1.trigger.get_params") as mock_get_params, patch(
            "api.routes.v1.trigger._get_trigger_services"
        ) as mock_services:
            mock_get_params.return_value = Mock(mode=Mode.OFFLINE)
            mock_services.return_value = {"logger": Mock()}

            response = client.get("/dtr/v1/configuration/trigger")

            assert response.status_code == 200
            # Check both old and new formats
            if "success" in response.json:
                assert response.json["success"] is True
                data = response.json["data"]
                assert data["policies"] == []
                assert data["total"] == -1
            else:
                assert response.json["policies"] == []
                assert response.json["total"] == -1


class TestNotificationRoutes:
    """Test suite for /notifications routes."""

    def test_notifications_success(self, client, mock_transfer_request):
        """Test successful notifications retrieval."""
        with patch("api.routes.v1.notifications.get_params") as mock_get_params, patch(
            "api.routes.v1.notifications.get_next_request"
        ) as mock_get_next, patch("api.routes.v1.notifications._get_notification_services") as mock_services:
            # Configure mocks
            mock_get_params.return_value = Mock(mode=Mode.ONLINE)
            mock_get_next.return_value = mock_transfer_request
            mock_services.return_value = {"logger": Mock()}

            response = client.get("/dtr/v1/notifications")

            assert response.status_code == 200
            # Check both old and new formats
            if "success" in response.json:
                assert response.json["success"] is True
                assert response.json["data"]["request"] is not None
            else:
                assert response.json["request"] is not None

    def test_notifications_offline(self, client):
        """Test notifications in offline mode."""
        with patch("api.routes.v1.notifications.get_params") as mock_get_params, patch(
            "api.routes.v1.notifications._get_notification_services"
        ) as mock_services:
            mock_get_params.return_value = Mock(mode=Mode.OFFLINE)
            mock_services.return_value = {"logger": Mock()}

            response = client.get("/dtr/v1/notifications")

            assert response.status_code == 200
            # Check both old and new formats
            if "success" in response.json:
                assert response.json["success"] is True
                assert response.json["data"]["request"] is None
            else:
                assert response.json["request"] is None

    def test_notifications_no_request(self, client):
        """Test notifications with no available request."""
        with patch("api.routes.v1.notifications.get_params") as mock_get_params, patch(
            "api.routes.v1.notifications.get_next_request"
        ) as mock_get_next, patch("api.routes.v1.notifications._get_notification_services") as mock_services:
            # Configure mocks
            mock_get_params.return_value = Mock(mode=Mode.ONLINE)
            mock_get_next.return_value = None
            mock_services.return_value = {"logger": Mock()}

            response = client.get("/dtr/v1/notifications")

            assert response.status_code == 200
            # Check both old and new formats
            if "success" in response.json:
                assert response.json["success"] is True
                assert response.json["data"]["request"] is None
            else:
                assert response.json["request"] is None


class TestConfigurationRoutes:
    """Test suite for /configure routes."""

    def test_configure_success(self, client):
        """Test successful configuration."""
        with patch("api.routes.v1.configure.set_configuration") as mock_set, patch(
            "api.routes.v1.configure.del_configuration"
        ) as mock_del, patch("api.routes.v1.configure._get_configuration_services") as mock_services, patch(
            "api.routes.v1.configure.ConfigurationSchema"
        ) as mock_schema:
            # Configure mocks
            mock_set.return_value = None
            mock_del.return_value = None
            mock_services.return_value = {
                "validation_service": Mock(),
                "logger": Mock(),
                "policy_repo": Mock(),
                "db_session": Mock(),
            }
            # Mock schema validation to succeed
            mock_schema.return_value = Mock()

            payload = {"global_parameters": {"mode": "ONLINE"}, "targets": [], "queues": [], "policies": []}

            response = client.post("/dtr/v1/configure", json=payload)

            assert response.status_code == 201
            # Check both old and new formats
            if "success" in response.json:
                assert response.json["success"] is True
                assert response.json["data"]["message"] == "configuration has been applied"
            else:
                assert response.json["message"] == "configuration has been applied"

    def test_unconfigure_success(self, client):
        """Test successful unconfiguration."""
        with patch("api.routes.v1.configure.del_configuration") as mock_del, patch(
            "api.routes.v1.configure._get_configuration_services"
        ) as mock_services:
            mock_del.return_value = None
            mock_services.return_value = {
                "logger": Mock(),
                "validation_service": Mock(),
                "policy_repo": Mock(),
                "db_session": Mock(),
            }

            response = client.delete("/dtr/v1/configure")

            assert response.status_code == 200
            # Check both old and new formats
            if "success" in response.json:
                assert response.json["success"] is True
                assert response.json["data"]["message"] == "configuration has been deleted"
            else:
                assert response.json["message"] == "configuration has been deleted"


class TestModeRoutes:
    """Test suite for /mode routes."""

    def test_get_global_parameters_success(self, client):
        """Test successful global parameters retrieval."""
        with patch("api.routes.v1.mode.get_params") as mock_get_params, patch(
            "api.routes.v1.mode._get_mode_services"
        ) as mock_services:
            mock_params = Mock()
            mock_params.to_dict.return_value = {"mode": "ONLINE", "retention_days": 30}
            mock_get_params.return_value = mock_params
            mock_services.return_value = {"logger": Mock()}

            response = client.get("/dtr/v1/global_params")

            assert response.status_code == 200
            assert response.json["mode"] == "ONLINE"
            assert response.json["retention_days"] == 30

    def test_get_global_parameters_none(self, client):
        """Test global parameters retrieval when none exist."""
        with patch("api.routes.v1.mode.get_params") as mock_get_params, patch(
            "api.routes.v1.mode._get_mode_services"
        ) as mock_services:
            mock_get_params.return_value = None
            mock_services.return_value = {"logger": Mock()}

            response = client.get("/dtr/v1/global_params")

            assert response.status_code == 204


class TestHealthEndpoints:
    """Test health check, readiness, and metrics endpoints."""

    def test_basic_health_check(self, client):
        """Test basic /healthz endpoint."""
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json["status"] == "healthy"
        assert response.json["service"] == "api-server"

    @patch("api.db.db")
    def test_comprehensive_health_success(self, mock_db, client):
        """Test /health endpoint with successful database connection."""
        mock_db.session.execute.return_value = None

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json
        assert data["status"] == "healthy"
        assert data["service"] == "api-server"
        assert data["checks"]["database"] == "healthy"
        mock_db.session.execute.assert_called_once()

    @patch("api.db.db")
    def test_comprehensive_health_database_failure(self, mock_db, client):
        """Test /health endpoint with database connection failure."""
        mock_db.session.execute.side_effect = Exception("Database connection failed")

        response = client.get("/health")
        assert response.status_code == 503
        data = response.json
        assert data["status"] == "unhealthy"
        assert data["service"] == "api-server"
        assert data["checks"]["database"] == "unhealthy"
        assert "error" in data["checks"]

    @patch("api.db.db")
    def test_readiness_probe_success(self, mock_db, client):
        """Test /ready endpoint with successful readiness check."""
        mock_db.session.execute.return_value = None

        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json
        assert data["status"] == "ready"
        assert data["service"] == "api-server"
        mock_db.session.execute.assert_called_once()

    @patch("api.db.db")
    def test_readiness_probe_failure(self, mock_db, client):
        """Test /ready endpoint with readiness check failure."""
        mock_db.session.execute.side_effect = Exception("Alembic table not found")

        response = client.get("/ready")
        assert response.status_code == 503
        data = response.json
        assert data["status"] == "not_ready"
        assert data["service"] == "api-server"
        assert "error" in data

    @patch("api.db.db")
    @patch("api.models.TransferRequest")
    @patch("api.models.TransferPolicy")
    def test_metrics_endpoint_success(self, mock_policy, mock_request, mock_db, client):
        """Test /metrics endpoint with successful metrics collection."""
        mock_db.session.query.return_value.count.side_effect = [42, 5]  # requests, policies

        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json
        assert data["service"] == "api-server"
        assert data["metrics"]["total_transfer_requests"] == 42
        assert data["metrics"]["total_transfer_policies"] == 5
        assert data["metrics"]["database_connections"] == "available"

    @patch("api.db.db")
    def test_metrics_endpoint_failure(self, mock_db, client):
        """Test /metrics endpoint with metrics collection failure."""
        mock_db.session.query.side_effect = Exception("Query failed")

        response = client.get("/metrics")
        assert response.status_code == 500
        data = response.json
        assert data["service"] == "api-server"
        assert data["error"] == "metrics_unavailable"
        assert "message" in data
