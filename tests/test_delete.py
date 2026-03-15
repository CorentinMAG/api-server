
from unittest.mock import patch
from api.services import QueueService
from api.exception import NotFoundException
import pytest
from api.services import (
    TargetService, QueueService, NotificationServerService,
    TransferPolicyService, TriggerService, WorkerService
)

PARAMETERS = [
    ("targets", TargetService),
    ("queues", QueueService),
    ("servers", NotificationServerService),
    ("policies", TransferPolicyService),
    ("triggers", TriggerService),
    ("workers", WorkerService)
]

class TestDelete:

    @pytest.mark.parametrize("endpoint, service", PARAMETERS)
    def test_delete(self, client, endpoint, service):
        with patch.object(service, "delete", return_value=True):
            response = client.delete(f"/api/v1/{endpoint}/1")
        assert response.status_code == 204

    @pytest.mark.parametrize("endpoint, service", PARAMETERS)
    def test_delete_not_found(self, client, endpoint, service):
        with patch.object(service, "delete", side_effect=NotFoundException("object with id 1 not found")):
            response = client.delete(f"/api/v1/{endpoint}/1")
        assert response.status_code == 404

