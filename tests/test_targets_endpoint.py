"""
Target endpoint tests.

Coverage for CRUD-style routes backed by TargetAPI.
"""

from __future__ import annotations

from unittest.mock import Mock, patch


def _make_paginated(items):
    pagination = Mock()
    pagination.model_dump.return_value = {
        "page": 1,
        "per_page": 20,
        "total": len(items),
    }
    paginated = Mock()
    paginated.items = items
    paginated.pagination = pagination
    return paginated


class TestTargetRoutes:
    def test_list_targets(self, client):
        from api.routes.v1.targets import TargetAPI

        target = Mock()
        target.to_dict.return_value = {"id": 1, "name": "primary-target"}
        mock_service = Mock()
        mock_service.paginate.return_value = _make_paginated([target])

        with patch.object(TargetAPI, "_get_or_create_service", return_value=mock_service):
            response = client.get("/api/v1/targets/")

        assert response.status_code == 200
        assert response.json["items"] == [{"id": 1, "name": "primary-target"}]

    def test_get_target_by_id(self, client):
        from api.routes.v1.targets import TargetAPI

        target = Mock()
        target.to_dict.return_value = {"id": 42, "name": "edge-target"}
        mock_service = Mock()
        mock_service.get_by_id.return_value = target

        with patch.object(TargetAPI, "_get_or_create_service", return_value=mock_service):
            response = client.get("/api/v1/targets/42")

        assert response.status_code == 200
        assert response.json == {"id": 42, "name": "edge-target"}

    def test_create_target(self, client):
        from api.routes.v1.targets import TargetAPI

        target = Mock()
        target.to_dict.return_value = {"id": 3, "name": "new-target"}
        mock_service = Mock()
        mock_service.create.return_value = target

        payload = {
            "name": "new-target",
            "protocol": "SFTP",
            "host": "sftp.example.com",
            "port": 22,
            "parameters": {"use_ssl": True, "verify": True},
        }

        with patch.object(TargetAPI, "_get_or_create_service", return_value=mock_service):
            response = client.post("/api/v1/targets/", json=payload)

        assert response.status_code == 200
        assert response.json == {"id": 3, "name": "new-target"}
        mock_service.commit.assert_called_once()

    def test_update_target(self, client):
        from api.routes.v1.targets import TargetAPI

        target = Mock()
        target.to_dict.return_value = {"id": 4, "name": "updated-target"}
        mock_service = Mock()
        mock_service.update.return_value = target

        with patch.object(TargetAPI, "_get_or_create_service", return_value=mock_service):
            response = client.put("/api/v1/targets/4", json={"name": "updated-target"})

        assert response.status_code == 200
        assert response.json == {"id": 4, "name": "updated-target"}
        mock_service.commit.assert_called_once()

    def test_delete_target(self, client):
        from api.routes.v1.targets import TargetAPI

        mock_service = Mock()

        with patch.object(TargetAPI, "_get_or_create_service", return_value=mock_service):
            response = client.delete("/api/v1/targets/9")

        assert response.status_code == 200
        mock_service.commit.assert_called_once()