
from unittest.mock import patch
from api.services import QueueService
from tests.factories.queues import (
    make_queue,
    make_mock_queue
)
from api.exception import NotFoundException
import pytest
from sqlalchemy.exc import IntegrityError

BASE_URL = "/api/v1/queues"

class TestPutQueue:


    def test_full_replace(self, client):
        payload = make_queue()
        queue = make_mock_queue(payload)

        with patch.object(QueueService, "update", return_value=queue):
            response = client.put(f"{BASE_URL}/1", json=payload)
        assert response.status_code == 200

    def test_partial_replace(self, client):
        data = {"priority": "10"}
        payload = make_queue(**data)
        queue = make_mock_queue(payload)

        with patch.object(QueueService, "update", return_value=queue):
            response = client.put(f"{BASE_URL}/1", json=data)
        assert response.status_code == 200
        assert response.json["priority"] == data["priority"]

    @pytest.mark.parametrize("error,status_code", [
        (
            IntegrityError("duplicates field in database", params=None, orig=IntegrityError),
            409
        ),
        (
            RuntimeError("No database Found"),
            500
        ),
        (
            NotFoundException("queue not found"),
            404
        )
    ])
    def test_update_with_error(self, client, error, status_code):
        payload = make_queue()

        with patch.object(QueueService, "update", side_effect=error):
            response = client.put(f"{BASE_URL}/1", json=payload)
        assert response.status_code == status_code

