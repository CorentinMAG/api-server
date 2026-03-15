
from unittest.mock import patch
from api.services import QueueService
from tests.factories.queues import (
    make_queue,
    make_mock_queue
)
from api.exception import NotFoundException

BASE_URL = "/api/v1/queues"

class TestListQueue:

    def test_get_existing_queue(self, client):
        payload = make_queue()
        queue = make_mock_queue(payload, id = 12)

        with patch.object(QueueService, "get_by_id", return_value=queue):
            response = client.get(f"{BASE_URL}/12")
        assert response.status_code == 200
        assert response.json["id"] == 12

        data = response.json
        del data["id"]
        assert data == payload

    def test_get_nonexisting_queue(self, client):
        with patch.object(QueueService, "get_by_id", side_effect=NotFoundException("Not Found queue")):
            response = client.get(f"{BASE_URL}/999")
        assert response.status_code == 404

