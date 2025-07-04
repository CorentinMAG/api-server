"""Unit tests for api.services.validation_service - Business rule validation testing"""
from __future__ import annotations

from unittest.mock import Mock

from dtr_common.constantes import State as StateEnum

from api.services.validation_service import ValidationService


class TestValidationService:
    """Test ValidationService functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_transfer_request_repo = Mock()
        self.mock_logger = Mock()
        self.validation_service = ValidationService(
            transfer_request_repo=self.mock_transfer_request_repo, logger=self.mock_logger
        )

    def test_can_purge_request_none(self):
        """Test purge validation with None request"""
        result = self.validation_service.can_purge_request(None)
        assert result is False

    def test_can_purge_request_all_successful(self):
        """Test purge validation when all associated requests are successful"""
        mock_request = Mock()
        mock_request.filename = "test.txt"
        mock_request.policy_id = 1
        mock_request.id = 1

        # Mock associated request with successful state
        mock_associated = Mock()
        mock_state = Mock()
        mock_state.state = StateEnum.SUCCESSFUL
        mock_associated.states = [mock_state]
        mock_associated.id = 2

        self.mock_transfer_request_repo.find_associated_requests.return_value = [mock_associated]

        result = self.validation_service.can_purge_request(mock_request)

        assert result is True
        self.mock_logger.debug.assert_called()

    def test_can_purge_request_not_all_successful(self):
        """Test purge validation when not all associated requests are successful"""
        mock_request = Mock()
        mock_request.filename = "test.txt"
        mock_request.policy_id = 1
        mock_request.id = 1

        # Mock associated request without successful state
        mock_associated = Mock()
        mock_state = Mock()
        mock_state.state = StateEnum.FAILED
        mock_associated.states = [mock_state]
        mock_associated.id = 2

        self.mock_transfer_request_repo.find_associated_requests.return_value = [mock_associated]

        result = self.validation_service.can_purge_request(mock_request)

        assert result is False

    def test_validate_file_for_policy_new_file(self):
        """Test file validation for new file"""
        self.mock_transfer_request_repo.get_existing_filenames_for_policy.return_value = set()

        result = self.validation_service.validate_file_for_policy(
            filename="new_file.txt", policy_id=1, only_new_data=True
        )

        assert result is True

    def test_validate_file_for_policy_existing_file_only_new_data(self):
        """Test file validation for existing file with only_new_data=True"""
        self.mock_transfer_request_repo.get_existing_filenames_for_policy.return_value = {"existing_file.txt"}

        result = self.validation_service.validate_file_for_policy(
            filename="existing_file.txt", policy_id=1, only_new_data=True
        )

        assert result is False

    def test_validate_file_for_policy_existing_file_finished(self):
        """Test file validation for existing file with finished requests"""
        self.mock_transfer_request_repo.get_existing_filenames_for_policy.return_value = {"existing_file.txt"}
        self.mock_transfer_request_repo.count_unfinished_requests_for_file.return_value = 0

        result = self.validation_service.validate_file_for_policy(
            filename="existing_file.txt", policy_id=1, only_new_data=False
        )

        assert result is True

    def test_validate_file_for_policy_existing_file_unfinished(self):
        """Test file validation for existing file with unfinished requests"""
        self.mock_transfer_request_repo.get_existing_filenames_for_policy.return_value = {"existing_file.txt"}
        self.mock_transfer_request_repo.count_unfinished_requests_for_file.return_value = 2

        result = self.validation_service.validate_file_for_policy(
            filename="existing_file.txt", policy_id=1, only_new_data=False
        )

        assert result is False

    def test_filter_valid_files(self):
        """Test filtering valid files"""
        filenames = ["file1.txt", "file2.txt", "file3.txt", "file4.txt"]

        # Mock existing files
        self.mock_transfer_request_repo.get_existing_filenames_for_policy.return_value = {
            "file2.txt",
            "file3.txt",
        }

        # Mock unfinished counts
        def mock_unfinished_count(policy_id, filename):
            if filename == "file2.txt":
                return 0  # finished
            elif filename == "file3.txt":
                return 1  # unfinished
            return 0

        self.mock_transfer_request_repo.count_unfinished_requests_for_file.side_effect = mock_unfinished_count

        result = self.validation_service.filter_valid_files(
            filenames=filenames, policy_id=1, only_new_data=False, max_files=10
        )

        # Should return: file1.txt (new), file2.txt (existing but finished)
        # Should exclude: file3.txt (existing and unfinished)
        assert "file1.txt" in result
        assert "file2.txt" in result
        assert "file3.txt" not in result
        assert "file4.txt" in result

    def test_filter_valid_files_max_limit(self):
        """Test filtering valid files with max limit"""
        filenames = ["file1.txt", "file2.txt", "file3.txt"]

        self.mock_transfer_request_repo.get_existing_filenames_for_policy.return_value = set()

        result = self.validation_service.filter_valid_files(
            filenames=filenames, policy_id=1, only_new_data=True, max_files=2
        )

        assert len(result) == 2

    def test_validate_policy_constraints_success(self):
        """Test successful policy constraint validation"""
        mock_policy = Mock()
        mock_policy.name = "test_policy"
        mock_policy.enabled = True
        mock_policy.dests = [Mock(), Mock()]

        is_valid, error_msg = self.validation_service.validate_policy_constraints(
            policy=mock_policy, num_files=5
        )

        assert is_valid is True
        assert error_msg == ""

    def test_validate_policy_constraints_no_policy(self):
        """Test policy constraint validation with None policy"""
        is_valid, error_msg = self.validation_service.validate_policy_constraints(policy=None, num_files=5)

        assert is_valid is False
        assert "not found" in error_msg

    def test_validate_policy_constraints_disabled(self):
        """Test policy constraint validation with disabled policy"""
        mock_policy = Mock()
        mock_policy.name = "test_policy"
        mock_policy.enabled = False

        is_valid, error_msg = self.validation_service.validate_policy_constraints(
            policy=mock_policy, num_files=5
        )

        assert is_valid is False
        assert "disabled" in error_msg

    def test_validate_policy_constraints_no_destinations(self):
        """Test policy constraint validation with no destinations"""
        mock_policy = Mock()
        mock_policy.name = "test_policy"
        mock_policy.enabled = True
        mock_policy.dests = []

        is_valid, error_msg = self.validation_service.validate_policy_constraints(
            policy=mock_policy, num_files=5
        )

        assert is_valid is False
        assert "No destinations" in error_msg

    def test_can_create_transfer_for_destination_success(self):
        """Test successful transfer creation validation"""
        self.mock_transfer_request_repo.find_in_progress_for_destination.return_value = None

        can_create, reason = self.validation_service.can_create_transfer_for_destination(
            policy_name="test_policy", filename="test.txt", dest_id=1
        )

        assert can_create is True
        assert reason == ""

    def test_can_create_transfer_for_destination_in_progress(self):
        """Test transfer creation validation with transfer in progress"""
        mock_existing = Mock()
        self.mock_transfer_request_repo.find_in_progress_for_destination.return_value = mock_existing

        can_create, reason = self.validation_service.can_create_transfer_for_destination(
            policy_name="test_policy", filename="test.txt", dest_id=1
        )

        assert can_create is False
        assert "already in progress" in reason
