"""
Test Targets endpoint
"""
from unittest.mock import Mock, patch
from tests.factories.targets import (
    make_targets, 
    make_target,
    make_mock_target,
    make_mock_targets
    )
from sqlalchemy.exc import IntegrityError

def _create_pagination(items):
    pagination = Mock()
    pagination.model_dump.return_value = {
        "page": 1,
        "per_page": 20,
        "total": len(items)
    }
    paginated = Mock()
    paginated.items = items
    paginated.pagination = pagination
    return paginated

BASE_URL = "/api/v1/targets"

class TestTargetRoutes:

    # def test_list_targets(self, client):
    #     from api.routes.v1.targets import TargetAPI

    #     targets = create_targets(50)

    #     mock_service = Mock()
    #     mock_service.paginate.return_value = _create_pagination([targets])

    #     with patch.object(TargetAPI, "service", new=mock_service):
    #         response = client.get(f"{BASE_URL}/")
    #     assert response.status_code == 200
        
    #     data = response.json
    #     items = data["items"]
    #     pagination = data["pagination"]

    #     assert pagination["total"] == len(targets)

    # def test_get_target_by_id(self, client):
    #     from api.routes.v1.targets import TargetAPI

    #     target = Mock()
    #     target.to_dict.return_value = {"id": 12, "name": "test_sftp"}
    #     mock_service = Mock()
    #     mock_service.get_by_id.return_value = target

    #     with patch.object(TargetAPI, "service", new=mock_service):
    #         response = client.get(f"{BASE_URL}/12")
    #     assert response.status_code == 200
    #     assert response.json == {"id": 12, "name": "test_sftp"}


    # def test_update_target(self, client):
    #     from api.routes.v1.targets import TargetAPI

    #     target = Mock()
    #     target.to_dict.return_value = {"id": 3, "name": "updated-target"}
    #     mock_service = Mock()
    #     mock_service.update.return_value = target

    #     with patch.object(TargetAPI, "service", new=mock_service):
    #         response = client.put(f"{BASE_URL}/4", json={"name": "updated-target"})
        
    #     assert response.status_code == 200
    #     assert response.json == {"id": 3, "name": "updated-target"}
    #     mock_service.commit.assert_called_once()

    # def test_delete_target(self, client):
    #     from api.routes.v1.targets import TargetAPI

    #     mock_service = Mock()

    #     with patch.object(TargetAPI, "service", new=mock_service):
    #         response = client.delete(f"{BASE_URL}/9")
    #     assert response.status_code == 200
    #     mock_service.commit.assert_called_once()
