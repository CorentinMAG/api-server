
from unittest.mock import patch
from api.services import TargetService
from tests.factories.targets import (
    make_targets,
    make_mock_targets
)
from tests.factories.common import make_mock_paginated
import pytest
from api.exception import MalformatedInputException

BASE_URL = "/api/v1/targets"

class TestPaginateTarget:

    @pytest.fixture(scope="class")
    def targets(self):
        payloads = make_targets(number = 60)
        return make_mock_targets(payloads)

    @pytest.mark.parametrize("page,page_size,total", [(1,10,60),(1,5,60),(2,10,60),(3,15,60)])
    def test_pagination(self, client, page, page_size, total, targets):
        first = (page - 1) * page_size
        last = page * page_size
        paginated = make_mock_paginated(page=page,page_size=page_size, total=60, items=targets[first:last])
        with patch.object(TargetService, "paginate", return_value=paginated):
            response = client.get(f"{BASE_URL}?page={page}&page_size={page_size}")
        assert response.status_code == 200
        data = response.json
        assert data["pagination"]["page"] == page
        assert data["pagination"]["page_size"] == page_size
        assert data["pagination"]["total"] == total
        assert len(data["items"]) == page_size
        assert data["items"] == [t.to_dict() for t in targets[first:last]]

    def test_get_all(self, client, targets):
        paginated = make_mock_paginated(page=1,page_size=10, total = 60, items=targets[:10])
        with patch.object(TargetService, "paginate", return_value=paginated):
            response = client.get(BASE_URL)
        assert response.status_code == 200
        data = response.json
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 10
        assert data["pagination"]["total"] == 60
        assert len(data["items"]) == 10
        assert data["items"] == [t.to_dict() for t in targets[:10]]
    
    def test_custom_page_size(self, client, targets):
        paginated = make_mock_paginated(page=1,page_size=5, total = 60, items=targets[:5])
        with patch.object(TargetService, "paginate", return_value=paginated):
            response = client.get(f"{BASE_URL}?page_size=5")
        assert response.status_code == 200
        data = response.json
        assert data["pagination"]["page_size"] == 5
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["total"] == 60
        assert len(data["items"]) == 5
        assert data["items"] == [t.to_dict() for t in targets[:5]]

    def test_custom_page(self, client, targets):
        paginated = make_mock_paginated(page=2,page_size=10, total = 60, items=targets[10:20])
        with patch.object(TargetService, "paginate", return_value=paginated):
            response = client.get(f"{BASE_URL}?page=2")
        assert response.status_code == 200
        data = response.json
        assert data["pagination"]["page_size"] == 10
        assert data["pagination"]["page"] == 2
        assert data["pagination"]["total"] == 60
        assert len(data["items"]) == 10
        assert data["items"] == [t.to_dict() for t in targets[10:20]]

    def test_custom_pagination(self, client, targets):
        paginated = make_mock_paginated(page=3,page_size=15, total = 60, items=targets[30:45])
        with patch.object(TargetService, "paginate", return_value=paginated):
            response = client.get(f"{BASE_URL}?page=3&page_size=15")
        assert response.status_code == 200
        data = response.json
        assert data["pagination"]["page_size"] == 15
        assert data["pagination"]["page"] == 3
        assert data["pagination"]["total"] == 60
        assert len(data["items"]) == 15
        assert data["items"] == [t.to_dict() for t in targets[30:45]]

    def test_out_of_page(self, client):
        paginated = make_mock_paginated(page=5,page_size=15, total = 10, items=[])
        with patch.object(TargetService, "paginate", return_value=paginated):
            response = client.get(f"{BASE_URL}?page=5")
        assert response.status_code == 200
        data = response.json
        assert data["pagination"]["page_size"] == 15
        assert data["pagination"]["total"] == 10
        assert data["pagination"]["page"] == 5
        assert len(data["items"]) == 0
        assert data["items"] == []

    def test_invalid_pagination_parameters(self, client):
        with patch.object(TargetService, "paginate", side_effect=MalformatedInputException):
            response = client.get(f"{BASE_URL}?page=abc&page_size=15")
        assert response.status_code == 422

