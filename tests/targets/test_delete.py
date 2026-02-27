
from unittest.mock import patch
from api.services import TargetService

BASE_URL = "/api/v1/targets"

class TestDeleteTarget:
    def test_delete_target(self, client):
        with patch.object(TargetService, "delete", return_value=True):
            response = client.delete(f"{BASE_URL}/1")
        assert response.status_code == 204
