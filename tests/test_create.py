import pytest
from unittest.mock import patch, Mock
from tests.payloads import (
    make_target,
    make_queue,
    make_server,
    make_trigger,
    make_worker,
    make_parameters,
)
from sqlalchemy.exc import IntegrityError
from api.services import (
    TargetService,
    QueueService,
    NotificationServerService,
    TransferPolicyService,
    TriggerService,
    WorkerService,
)

PARAMETERS = [
    ("targets", make_target, TargetService),
    ("queues", make_queue, QueueService),
    ("servers", make_server, NotificationServerService),
    ("triggers", make_trigger, TriggerService),
    ("workers", make_worker, WorkerService),
]


class TestCreateAPI:

    @pytest.mark.parametrize("endpoint, make_factory, service", PARAMETERS)
    def test_create(self, client, make_factory, endpoint, service):
        payload = make_factory()

        mock = Mock()
        mock.to_dict.return_value = {"id": 1, **payload}

        with patch.object(service, "create", return_value=mock):
            response = client.post(f"/api/v1/{endpoint}", json=payload)

        assert response.status_code == 201
        assert response.json == mock.to_dict()
        mock.assert_called_once()

    # @pytest.mark.parametrize("missing_field", ["name", "protocol", "host", "port"])
    # def test_create_with_missing_field(self, client, missing_field):
    #     payload = make_target()
    #     del payload[missing_field]

    #     response = client.post(BASE_URL, json = payload)

    #     assert response.status_code == 422

    # @pytest.mark.parametrize("error,status_code", [
    #     (
    #         IntegrityError("duplicates field in database", params=None, orig=IntegrityError),
    #         409
    #     ),
    #     (
    #         RuntimeError("No database Found"),
    #         500
    #     )
    # ])
    # def test_create_with_error(self, client, error, status_code):
    #     payload = make_target()

    #     with patch.object(TargetService, "create", side_effect=error):
    #         response = client.post(BASE_URL, json=payload)
    #     assert response.status_code == status_code
