"""Unit tests for api.services.queue_service - Queue management testing"""

from __future__ import annotations

from unittest.mock import Mock

from api.services.queue_service import QueueCapacityInfo, QueueService


class TestQueueService:
    """Test QueueService functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_transfer_request_repo = Mock()
        self.mock_logger = Mock()
        self.queue_service = QueueService(
            transfer_request_repo=self.mock_transfer_request_repo, logger=self.mock_logger
        )

    def test_check_queue_capacity_normal(self):
        """Test normal queue capacity checking"""
        # Mock policy with 50 queued requests, limit 100
        self.mock_transfer_request_repo.count_queued_requests_for_policy.return_value = 50

        # Mock queue
        mock_queue = Mock()
        mock_queue.queue_limit = 100
        mock_queue.queue_threshold = 80

        result = self.queue_service.check_queue_capacity(
            policy_id=1, queue=mock_queue, num_destinations=2, num_triggered_files=10
        )

        assert isinstance(result, QueueCapacityInfo)
        assert result.available_slots == 50  # 100 - 50
        assert result.queued_count == 50
        assert result.max_files_per_destination == 25  # 50 / 2
        assert result.is_full is False
        assert result.is_near_threshold is False  # 50 + 10 < 80

    def test_check_queue_capacity_full(self):
        """Test queue capacity when queue is full"""
        # Mock policy with 98 queued requests, limit 100, 2 destinations
        self.mock_transfer_request_repo.count_queued_requests_for_policy.return_value = 98

        mock_queue = Mock()
        mock_queue.queue_limit = 100
        mock_queue.queue_threshold = 80

        result = self.queue_service.check_queue_capacity(
            policy_id=1, queue=mock_queue, num_destinations=2, num_triggered_files=5
        )

        assert result.available_slots == 2  # 100 - 98
        assert result.queued_count == 98
        assert result.max_files_per_destination == 0  # Not enough space
        assert result.is_full is True  # 2 <= 2 destinations
        assert result.is_near_threshold is True  # 98 + 5 > 80

    def test_check_queue_capacity_near_threshold(self):
        """Test queue capacity when near threshold"""
        self.mock_transfer_request_repo.count_queued_requests_for_policy.return_value = 70

        mock_queue = Mock()
        mock_queue.queue_limit = 100
        mock_queue.queue_threshold = 80

        result = self.queue_service.check_queue_capacity(
            policy_id=1,
            queue=mock_queue,
            num_destinations=2,
            num_triggered_files=15,  # 70 + 15 = 85 > 80
        )

        assert result.is_near_threshold is True

    def test_log_queue_warning_if_needed(self):
        """Test queue warning logging"""
        mock_queue = Mock()
        mock_queue.name = "test_queue"
        mock_queue.queue_limit = 100

        capacity_info = QueueCapacityInfo(
            available_slots=10,
            queued_count=90,
            max_files_per_destination=5,
            is_full=False,
            is_near_threshold=True,
        )

        self.queue_service.log_queue_warning_if_needed(capacity_info, mock_queue)

        # Verify warning was logged
        self.mock_logger.warning.assert_called_once()
        args = self.mock_logger.warning.call_args[0]
        assert "test_queue" in args[1]
        assert args[2] == 90  # queued_count
        assert args[3] == 100  # queue_limit

    def test_log_queue_warning_not_needed(self):
        """Test that warning is not logged when not near threshold"""
        mock_queue = Mock()

        capacity_info = QueueCapacityInfo(
            available_slots=50,
            queued_count=50,
            max_files_per_destination=25,
            is_full=False,
            is_near_threshold=False,
        )

        self.queue_service.log_queue_warning_if_needed(capacity_info, mock_queue)

        # Verify warning was NOT logged
        self.mock_logger.warning.assert_not_called()

    def test_can_accept_files_true(self):
        """Test can_accept_files returns True when capacity allows"""
        self.mock_transfer_request_repo.count_queued_requests_for_policy.return_value = 20

        mock_queue = Mock()
        mock_queue.queue_limit = 100
        mock_queue.queue_threshold = 80

        result = self.queue_service.can_accept_files(
            policy_id=1, queue=mock_queue, num_destinations=2, num_files=10
        )

        assert result is True

    def test_can_accept_files_false(self):
        """Test can_accept_files returns False when capacity doesn't allow"""
        self.mock_transfer_request_repo.count_queued_requests_for_policy.return_value = 98

        mock_queue = Mock()
        mock_queue.queue_limit = 100
        mock_queue.queue_threshold = 80

        result = self.queue_service.can_accept_files(
            policy_id=1, queue=mock_queue, num_destinations=2, num_files=5
        )

        assert result is False

    def test_get_max_processable_files(self):
        """Test getting maximum processable files"""
        self.mock_transfer_request_repo.count_queued_requests_for_policy.return_value = 30

        mock_queue = Mock()
        mock_queue.queue_limit = 100
        mock_queue.queue_threshold = 80

        result = self.queue_service.get_max_processable_files(
            policy_id=1, queue=mock_queue, num_destinations=5
        )

        # Available slots: 100 - 30 = 70
        # Max files per destination: 70 / 5 = 14
        assert result == 14
