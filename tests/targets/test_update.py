
from unittest.mock import patch
from api.services import TargetService
from tests.factories.targets import (
    make_target,
    make_mock_target
)
from api.exception import NotFoundException
import pytest
from sqlalchemy.exc import IntegrityError

BASE_URL = "/api/v1/targets"

class TestPutTarget:


    def test_full_replace(self, client):
        payload = make_target()
        target = make_mock_target(payload)

        with patch.object(TargetService, "update", return_value=target):
            response = client.put(f"{BASE_URL}/1", json=payload)
        assert response.status_code == 200

    def test_partial_replace(self, client):
        data = {"host": "1.1.1.1"}
        payload = make_target(**data)
        target = make_mock_target(payload)

        with patch.object(TargetService, "update", return_value=target):
            response = client.put(f"{BASE_URL}/1", json=data)
        assert response.status_code == 200
        assert response.json["host"] == "1.1.1.1"

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
            NotFoundException("Target not found"),
            404
        )
    ])
    def test_update_with_error(self, client, error, status_code):
        payload = make_target()

        with patch.object(TargetService, "update", side_effect=error):
            response = client.put(f"{BASE_URL}/1", json=payload)
        assert response.status_code == status_code

