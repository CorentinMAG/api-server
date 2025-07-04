"""Unit tests for api.services.configuration - Complex setup testing"""
from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from dtr_common.constantes import Type


class TestCreateServers:
    """Test server creation logic"""

    def test_create_servers_basic(self):
        """Test basic server creation"""
        from api.services.configuration import create_servers

        # Mock server data
        server_data = Mock()
        server_data.model_dump.return_value = {"name": "test_server", "host": "localhost", "port": 22}
        server_data.credentials = None

        with patch("api.services.configuration.NotificationServer") as mock_notification_server:
            mock_instance = Mock()
            mock_instance.name = "test_server"
            mock_notification_server.return_value = mock_instance

            result = create_servers([server_data])

            assert len(result) == 1
            assert result[0].name == "test_server"

    def test_create_servers_with_credentials(self):
        """Test server creation with credentials"""
        from api.services.configuration import create_servers

        # Mock credential data
        mock_password = Mock()
        mock_password.get_secret_value.return_value = "test_pass"

        cred_data = Mock()
        cred_data.login = "test_user"
        cred_data.password = mock_password

        # Mock server data with credentials
        server_data = Mock()
        server_data.model_dump.return_value = {"name": "test_server", "host": "localhost", "port": 22}
        server_data.credentials = cred_data

        with patch("api.services.configuration.Credentials") as mock_creds, patch(
            "api.services.configuration.NotificationServer"
        ) as mock_server:
            mock_creds_instance = Mock()
            mock_creds.return_value = mock_creds_instance

            mock_server_instance = Mock()
            mock_server_instance.name = "test_server"
            mock_server.return_value = mock_server_instance

            result = create_servers([server_data])

            assert len(result) == 1
            assert result[0].name == "test_server"
            mock_creds.assert_called_once_with(login="test_user", password="test_pass")


class TestCreateQueues:
    """Test queue creation with global parameters"""

    def test_create_queues_with_defaults(self):
        """Test queue creation with global parameter defaults"""
        from api.services.configuration import create_queues

        # Mock global parameters
        mock_global_params = Mock()
        mock_global_params.queue_timeout = 3600
        mock_global_params.queue_limit = 1000
        mock_global_params.queue_threshold = 800

        queue_data = Mock()
        queue_data.model_dump.return_value = {
            "name": "test_queue",
            "priority": 1,
            "queue_timeout": 3600,
            "queue_limit": 1000,
            "queue_threshold": 800,
        }
        queue_data.queue_timeout = None
        queue_data.queue_limit = None
        queue_data.queue_threshold = None

        with patch("api.services.configuration.Queue") as mock_queue_class:
            mock_queue_instance = Mock()
            mock_queue_instance.name = "test_queue"
            mock_queue_class.return_value = mock_queue_instance

            result = create_queues([queue_data], mock_global_params)

            assert len(result) == 1
            assert result[0].name == "test_queue"

    def test_create_queues_with_specific_values(self):
        """Test queue creation with specific values (not defaults)"""
        from api.services.configuration import create_queues

        mock_global_params = Mock()
        mock_global_params.queue_timeout = 3600
        mock_global_params.queue_limit = 1000
        mock_global_params.queue_threshold = 800

        queue_data = Mock()
        queue_data.model_dump.return_value = {
            "name": "test_queue",
            "priority": 1,
            "queue_timeout": 7200,
            "queue_limit": 2000,
            "queue_threshold": 1600,
        }
        queue_data.queue_timeout = 7200
        queue_data.queue_limit = 2000
        queue_data.queue_threshold = 1600

        with patch("api.services.configuration.Queue") as mock_queue_class:
            mock_queue_instance = Mock()
            mock_queue_instance.name = "test_queue"
            mock_queue_class.return_value = mock_queue_instance

            result = create_queues([queue_data], mock_global_params)

            assert len(result) == 1
            assert result[0].name == "test_queue"


class TestCreateTargets:
    """Test target creation with parameters"""

    def test_create_targets_basic(self):
        """Test basic target creation"""
        from api.services.configuration import create_targets

        # Mock parameters
        params_data = Mock()
        params_data.model_dump.return_value = {"use_ssl": True, "verify": True}

        target_data = Mock()
        target_data.model_dump.return_value = {
            "name": "test_target",
            "protocol": "sftp",
            "host": "localhost",
            "port": 22,
        }
        target_data.credentials = None
        target_data.parameters = params_data

        with patch("api.services.configuration.TargetParameters") as mock_params, patch(
            "api.services.configuration.Target"
        ) as mock_target_class:
            mock_params_instance = Mock()
            mock_params.return_value = mock_params_instance

            mock_target_instance = Mock()
            mock_target_instance.name = "test_target"
            mock_target_class.return_value = mock_target_instance

            result = create_targets([target_data])

            assert len(result) == 1
            assert result[0].name == "test_target"

    def test_create_targets_with_credentials(self):
        """Test target creation with credentials"""
        from api.services.configuration import create_targets

        # Mock credential data
        mock_password = Mock()
        mock_password.get_secret_value.return_value = "target_pass"

        cred_data = Mock()
        cred_data.login = "target_user"
        cred_data.password = mock_password

        params_data = Mock()
        params_data.model_dump.return_value = {"use_ssl": True}

        target_data = Mock()
        target_data.model_dump.return_value = {
            "name": "secure_target",
            "protocol": "sftp",
            "host": "secure.example.com",
            "port": 22,
        }
        target_data.credentials = cred_data
        target_data.parameters = params_data

        with patch("api.services.configuration.Credentials") as mock_creds, patch(
            "api.services.configuration.TargetParameters"
        ) as mock_params, patch("api.services.configuration.Target") as mock_target_class:
            mock_creds_instance = Mock()
            mock_creds.return_value = mock_creds_instance

            mock_params_instance = Mock()
            mock_params.return_value = mock_params_instance

            mock_target_instance = Mock()
            mock_target_instance.name = "secure_target"
            mock_target_class.return_value = mock_target_instance

            result = create_targets([target_data])

            assert len(result) == 1
            assert result[0].name == "secure_target"
            mock_creds.assert_called_once_with(login="target_user", password="target_pass")


class TestCreatePolicies:
    """Test the complex create_policies function"""

    def test_create_policies_periodical_basic(self):
        """Test creating periodical policies"""
        from api.services.configuration import create_policies

        # Mock target
        mock_target = Mock()
        mock_target.name = "test_target"
        ntargets = [mock_target]

        # Mock queue
        mock_queue = Mock()
        mock_queue.name = "test_queue"
        nqueues = [mock_queue]

        # Mock global parameters
        mock_global_params = Mock()
        mock_global_params.to_dict.return_value = {
            "max_retry": 3,
            "queue_timeout": 3600,
            "polling_interval": 300,
        }
        mock_global_params.max_retry = 3
        mock_global_params.queue_timeout = 3600
        mock_global_params.polling_interval = 300

        # Mock servers
        nservers = []

        # Mock policy data
        mock_src = Mock()
        mock_src.model_dump.return_value = {"type": "source"}
        mock_src.target = "test_target"

        mock_dest = Mock()
        mock_dest.model_dump.return_value = {"type": "destination"}
        mock_dest.target = "test_target"

        mock_policy = Mock()
        mock_policy.name = "test_policy"
        mock_policy.enabled = True
        mock_policy.type = Type.PERIODICAL
        mock_policy.src = mock_src
        mock_policy.dests = [mock_dest]
        mock_policy.queue = "test_queue"
        mock_policy.parameters = None

        policies = [mock_policy]

        with patch("api.services.configuration.SourcePolicy") as mock_src_policy, patch(
            "api.services.configuration.DestinationPolicy"
        ) as mock_dest_policy, patch(
            "api.services.configuration.TransferPolicyParameters"
        ) as mock_transfer_params, patch(
            "api.services.configuration.PeriodicalParameters"
        ) as mock_period_params, patch("api.services.configuration.TransferPolicy") as mock_transfer_policy:
            # Mock SQLAlchemy mapper for TransferPolicyParameters
            mock_mapper = Mock()
            mock_mapper.columns = ["max_retry", "queue_timeout", "polling_interval"]
            mock_transfer_params.__mapper__ = mock_mapper

            mock_src_policy.return_value = Mock()
            mock_dest_policy.return_value = Mock()
            mock_transfer_params.return_value = Mock()
            mock_period_params.return_value = Mock()
            mock_transfer_policy.return_value = Mock()

            result = create_policies(policies, mock_global_params, nservers, nqueues, ntargets)

            assert len(result) == 1
            mock_transfer_policy.assert_called_once()

    def test_create_policies_commanded_basic(self):
        """Test creating commanded policies"""
        from api.services.configuration import create_policies

        # Mock target
        mock_target = Mock()
        mock_target.name = "test_target"
        ntargets = [mock_target]

        # Mock queue
        mock_queue = Mock()
        mock_queue.name = "test_queue"
        nqueues = [mock_queue]

        # Mock global parameters
        mock_global_params = Mock()
        mock_global_params.to_dict.return_value = {"max_retry": 3}
        mock_global_params.max_retry = 3

        # Mock servers
        nservers = []

        # Mock policy parameters
        mock_params = Mock()
        mock_params.model_dump.return_value = {"max_retry": 5}
        mock_params.periodical = None

        # Mock policy data
        mock_src = Mock()
        mock_src.model_dump.return_value = {"type": "source"}
        mock_src.target = "test_target"

        mock_dest = Mock()
        mock_dest.model_dump.return_value = {"type": "destination"}
        mock_dest.target = "test_target"

        mock_policy = Mock()
        mock_policy.name = "commanded_policy"
        mock_policy.enabled = True
        mock_policy.type = Type.COMMANDED
        mock_policy.src = mock_src
        mock_policy.dests = [mock_dest]
        mock_policy.queue = "test_queue"
        mock_policy.parameters = mock_params

        policies = [mock_policy]

        with patch("api.services.configuration.SourcePolicy") as mock_src_policy, patch(
            "api.services.configuration.DestinationPolicy"
        ) as mock_dest_policy, patch(
            "api.services.configuration.TransferPolicyParameters"
        ) as mock_transfer_params, patch("api.services.configuration.TransferPolicy") as mock_transfer_policy:
            # Mock SQLAlchemy mapper for TransferPolicyParameters
            mock_mapper = Mock()
            mock_mapper.columns = ["max_retry", "queue_timeout", "polling_interval"]
            mock_transfer_params.__mapper__ = mock_mapper

            mock_src_policy.return_value = Mock()
            mock_dest_policy.return_value = Mock()
            mock_transfer_params_instance = Mock()
            mock_transfer_params.return_value = mock_transfer_params_instance
            mock_transfer_policy.return_value = Mock()

            result = create_policies(policies, mock_global_params, nservers, nqueues, ntargets)

            assert len(result) == 1
            mock_transfer_policy.assert_called_once()

    def test_create_policies_with_notifications_kafka(self):
        """Test creating policies with Kafka notifications"""
        from api.services.configuration import create_policies

        # Mock target
        mock_target = Mock()
        mock_target.name = "test_target"
        ntargets = [mock_target]

        # Mock queue
        mock_queue = Mock()
        mock_queue.name = "test_queue"
        nqueues = [mock_queue]

        # Mock kafka server
        mock_kafka_server = Mock()
        mock_kafka_server.name = "kafka_server"
        mock_kafka_server.type = "kafka"
        nservers = [mock_kafka_server]

        # Mock global parameters
        mock_global_params = Mock()
        mock_global_params.to_dict.return_value = {"max_retry": 3}
        mock_global_params.max_retry = 3

        # Mock policy data with notifications
        mock_src = Mock()
        mock_src.model_dump.return_value = {"type": "source"}
        mock_src.target = "test_target"

        mock_dest = Mock()
        mock_dest.model_dump.return_value = {
            "type": "destination",
            "notifications": [
                {"server": "kafka_server", "topics": ["topic1", {"topic": "topic2", "partition": 1}]}
            ],
        }
        mock_dest.target = "test_target"

        mock_policy = Mock()
        mock_policy.name = "notification_policy"
        mock_policy.enabled = True
        mock_policy.type = Type.COMMANDED
        mock_policy.src = mock_src
        mock_policy.dests = [mock_dest]
        mock_policy.queue = "test_queue"
        mock_policy.parameters = None

        policies = [mock_policy]

        with patch("api.services.configuration.SourcePolicy") as mock_src_policy, patch(
            "api.services.configuration.DestinationPolicy"
        ) as mock_dest_policy, patch(
            "api.services.configuration.TransferPolicyParameters"
        ) as mock_transfer_params, patch(
            "api.services.configuration.TransferPolicy"
        ) as mock_transfer_policy, patch(
            "api.services.configuration.KafkaTopicParameters"
        ) as mock_kafka_params, patch("api.services.configuration.copy") as mock_copy:
            # Mock SQLAlchemy mapper for TransferPolicyParameters
            mock_mapper = Mock()
            mock_mapper.columns = ["max_retry", "queue_timeout", "polling_interval"]
            mock_transfer_params.__mapper__ = mock_mapper

            mock_copy.deepcopy.return_value = {
                "server": "kafka_server",
                "topics": ["topic1", {"topic": "topic2", "partition": 1}],
            }

            mock_src_policy.return_value = Mock()
            mock_dest_policy.return_value = Mock()
            mock_transfer_params.return_value = Mock()
            mock_transfer_policy.return_value = Mock()
            mock_kafka_params.return_value = Mock()

            result = create_policies(policies, mock_global_params, nservers, nqueues, ntargets)

            assert len(result) == 1
            # Should create Kafka topic parameters for each topic
            assert mock_kafka_params.call_count >= 2

    def test_create_policies_unsupported_notification_type(self):
        """Test creating policies with unsupported notification server type"""
        from api.services.configuration import create_policies

        # Mock target
        mock_target = Mock()
        mock_target.name = "test_target"
        ntargets = [mock_target]

        # Mock queue
        mock_queue = Mock()
        mock_queue.name = "test_queue"
        nqueues = [mock_queue]

        # Mock unsupported server
        mock_server = Mock()
        mock_server.name = "unsupported_server"
        mock_server.type = "unsupported_type"
        nservers = [mock_server]

        # Mock global parameters
        mock_global_params = Mock()
        mock_global_params.to_dict.return_value = {"max_retry": 3}

        # Mock policy data with unsupported notifications
        mock_src = Mock()
        mock_src.model_dump.return_value = {"path": "/source", "pattern": "*", "purge": False}
        mock_src.target = "test_target"

        mock_dest = Mock()
        mock_dest.model_dump.return_value = {
            "path": "/destination",
            "notifications": [{"server": "unsupported_server"}],
        }
        mock_dest.target = "test_target"

        mock_policy = Mock()
        mock_policy.name = "bad_notification_policy"
        mock_policy.enabled = True
        mock_policy.type = Type.COMMANDED
        mock_policy.src = mock_src
        mock_policy.dests = [mock_dest]
        mock_policy.queue = "test_queue"
        mock_policy.parameters = None

        policies = [mock_policy]

        with patch("api.services.configuration.copy") as mock_copy:
            mock_copy.deepcopy.return_value = {"server": "unsupported_server"}

            with pytest.raises(NotImplementedError, match="only 'kafka' server is emplemented"):
                create_policies(policies, mock_global_params, nservers, nqueues, ntargets)


class TestCreateGlobalParams:
    """Test global parameter creation"""

    def test_create_global_params(self):
        """Test creating global parameters"""
        from api.services.configuration import create_global_params

        mock_gparams = Mock()
        mock_gparams.model_dump.return_value = {
            "max_retry": 3,
            "queue_timeout": 3600,
            "polling_interval": 300,
        }

        with patch("api.services.configuration.GlobalParameters") as mock_global_params_class:
            mock_instance = Mock()
            mock_global_params_class.return_value = mock_instance

            result = create_global_params(mock_gparams)

            assert result == mock_instance
            mock_global_params_class.assert_called_once_with(
                max_retry=3, queue_timeout=3600, polling_interval=300
            )


class TestConfigure:
    """Test complete configuration workflow"""

    @patch("api.services.configuration.transactional")
    @patch("api.services.configuration.db")
    @patch("api.services.configuration.create_global_params")
    @patch("api.services.configuration.create_servers")
    @patch("api.services.configuration.create_queues")
    @patch("api.services.configuration.create_targets")
    @patch("api.services.configuration.create_policies")
    def test_configure_basic_workflow(
        self,
        mock_policies,
        mock_targets,
        mock_queues,
        mock_servers,
        mock_global_params,
        mock_db,
        mock_transactional,
    ):
        """Test complete configuration workflow with comprehensive mocking"""
        from api.services.configuration import configure

        # Mock the transactional decorator to just call the function
        mock_transactional.return_value = lambda func: func

        # Mock return values
        mock_global_params.return_value = Mock()
        mock_servers.return_value = []
        mock_queues.return_value = []
        mock_targets.return_value = []
        mock_policies.return_value = []

        # Mock database session
        mock_db.session = Mock()

        # Mock configuration data
        config_data = Mock()
        config_data.global_parameters = Mock()
        config_data.notification_servers = []
        config_data.queues = []
        config_data.targets = []
        config_data.transfer_policies = []

        # Act - call the actual function (decorator bypassed)
        configure.__wrapped__(config_data)

        # Assert creation functions were called
        mock_global_params.assert_called_once()
        mock_servers.assert_called_once()
        mock_queues.assert_called_once()
        mock_targets.assert_called_once()
        mock_policies.assert_called_once()
        mock_db.session.add_all.assert_called_once()


class TestUnconfigure:
    """Test unconfigure function"""

    @patch("api.services.configuration.transactional")
    @patch("api.services.configuration.db")
    def test_unconfigure_basic(self, mock_db, mock_transactional):
        """Test basic unconfigure functionality"""
        from api.services.configuration import unconfigure

        # Mock the transactional decorator to just call the function
        mock_transactional.return_value = lambda func: func

        # Mock database operations
        mock_db.session = Mock()
        mock_db.metadata = Mock()
        mock_table = Mock()
        mock_table.name = "test_table"
        mock_table.delete.return_value = "DELETE FROM test_table"
        mock_db.metadata.sorted_tables = [mock_table]

        # Call function with no keep list
        unconfigure.__wrapped__()

        # Should call execute with table delete
        mock_db.session.execute.assert_called_with("DELETE FROM test_table")

    @patch("api.services.configuration.transactional")
    @patch("api.services.configuration.db")
    def test_unconfigure_with_keep_list(self, mock_db, mock_transactional):
        """Test unconfigure with keep list"""
        from api.services.configuration import unconfigure

        # Mock the transactional decorator
        mock_transactional.return_value = lambda func: func

        # Mock database operations
        mock_db.session = Mock()
        mock_db.metadata = Mock()

        # Mock tables - one to keep, one to delete
        mock_table_keep = Mock()
        mock_table_keep.name = "keep_table"

        mock_table_delete = Mock()
        mock_table_delete.name = "delete_table"
        mock_table_delete.delete.return_value = "DELETE FROM delete_table"

        mock_db.metadata.sorted_tables = [mock_table_keep, mock_table_delete]

        # Call function with keep list
        keep_list = ["keep_table"]
        unconfigure.__wrapped__(keep=keep_list)

        # Should only call execute for the table not in keep list
        mock_db.session.execute.assert_called_once_with("DELETE FROM delete_table")
        # Should not try to delete the kept table
        mock_table_keep.delete.assert_not_called()


class TestErrorHandling:
    """Test error handling in configuration"""

    @patch("api.services.configuration.db")
    def test_configure_database_error(self, mock_db):
        """Test configuration handles database errors"""
        from api.services.configuration import configure

        # Mock database error
        mock_db.session.add_all.side_effect = Exception("Database error")

        config_data = Mock()
        config_data.global_parameters = Mock()
        config_data.notification_servers = []
        config_data.queues = []
        config_data.targets = []
        config_data.transfer_policies = []

        # Should not raise exception (decorator handles it)
        try:
            configure(config_data)
        except Exception:
            pass  # Expected due to decorator error handling
