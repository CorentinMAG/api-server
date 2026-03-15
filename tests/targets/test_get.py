
from unittest.mock import patch
from api.services import TargetService
from tests.factories.targets import (
    make_target,
    make_mock_target
)
from api.exception import NotFoundException

BASE_URL = "/api/v1/targets"

class TestListTarget:

    def test_get_existing_target(self, client):
        payload = make_target()
        target = make_mock_target(payload, id = 12)

        with patch.object(TargetService, "get_by_id", return_value=target):
            response = client.get(f"{BASE_URL}/12")
        assert response.status_code == 200
        assert response.json["id"] == 12

        data = response.json
        del data["id"]
        assert data == payload

    def test_get_nonexisting_target(self, client):
        with patch.object(TargetService, "get_by_id", side_effect=NotFoundException("Not Found Target")):
            response = client.get(f"{BASE_URL}/999")
        assert response.status_code == 404

