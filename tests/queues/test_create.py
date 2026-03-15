
import pytest
from unittest.mock import patch
from tests.factories.queues import (
    make_queue,
    make_mock_queue
)
from sqlalchemy.exc import IntegrityError
from api.services import QueueService

BASE_URL = "/api/v1/queues"

class TestCreateQueue:

    def test_create_queue(self, client):
        payload = make_queue()
        queue = make_mock_queue(payload)

        with patch.object(QueueService, "create", return_value=queue):
            response = client.post(BASE_URL, json = payload)
        assert response.status_code == 201
        assert response.json == queue.to_dict()

    @pytest.mark.parametrize("missing_field", ["name"])
    def test_create_with_missing_field(self, client, missing_field):
        payload = make_queue()
        del payload[missing_field]
        response = client.post(BASE_URL, json = payload)

        assert response.status_code == 422

    @pytest.mark.parametrize("error,status_code", [
        (
            IntegrityError("duplicates field in database", params=None, orig=IntegrityError),
            409
        ),
        (
            RuntimeError("No database Found"),
            500
        )
    ])
    def test_create_with_error(self, client, error, status_code):
        payload = make_queue()

        with patch.object(QueueService, "create", side_effect=error):
            response = client.post(BASE_URL, json=payload)
        assert response.status_code == status_code
