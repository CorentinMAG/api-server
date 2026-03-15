
from unittest.mock import patch
from api.services import QueueService
from tests.factories.queues import (
    make_queues,
    make_mock_queues
)
from tests.factories.common import make_mock_paginated
import pytest
from api.exception import MalformatedInputException

BASE_URL = "/api/v1/queues"

class TestPaginateQueue:

    @pytest.fixture(scope="class")
    def queues(self):
        payloads = make_queues(number = 60)
        return make_mock_queues(payloads)

    @pytest.mark.parametrize("page,page_size,total", [(1,10,60),(1,5,60),(2,10,60),(3,15,60)])
    def test_pagination(self, client, page, page_size, total, queues):
        first = (page - 1) * page_size
        last = page * page_size
        paginated = make_mock_paginated(page=page,page_size=page_size, total=60, items=queues[first:last])
        with patch.object(QueueService, "paginate", return_value=paginated):
            response = client.get(f"{BASE_URL}?page={page}&page_size={page_size}")
        assert response.status_code == 200
        data = response.json
        assert data["pagination"]["page"] == page
        assert data["pagination"]["page_size"] == page_size
        assert data["pagination"]["total"] == total
        assert len(data["items"]) == page_size
        assert data["items"] == [t.to_dict() for t in queues[first:last]]

    def test_get_all(self, client, queues):
        paginated = make_mock_paginated(page=1,page_size=10, total = 60, items=queues[:10])
        with patch.object(QueueService, "paginate", return_value=paginated):
            response = client.get(BASE_URL)
        assert response.status_code == 200
        data = response.json
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 10
        assert data["pagination"]["total"] == 60
        assert len(data["items"]) == 10
        assert data["items"] == [t.to_dict() for t in queues[:10]]
    
    def test_custom_page_size(self, client, queues):
        paginated = make_mock_paginated(page=1,page_size=5, total = 60, items=queues[:5])
        with patch.object(QueueService, "paginate", return_value=paginated):
            response = client.get(f"{BASE_URL}?page_size=5")
        assert response.status_code == 200
        data = response.json
        assert data["pagination"]["page_size"] == 5
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["total"] == 60
        assert len(data["items"]) == 5
        assert data["items"] == [t.to_dict() for t in queues[:5]]

    def test_custom_page(self, client, queues):
        paginated = make_mock_paginated(page=2,page_size=10, total = 60, items=queues[10:20])
        with patch.object(QueueService, "paginate", return_value=paginated):
            response = client.get(f"{BASE_URL}?page=2")
        assert response.status_code == 200
        data = response.json
        assert data["pagination"]["page_size"] == 10
        assert data["pagination"]["page"] == 2
        assert data["pagination"]["total"] == 60
        assert len(data["items"]) == 10
        assert data["items"] == [t.to_dict() for t in queues[10:20]]

    def test_custom_pagination(self, client, queues):
        paginated = make_mock_paginated(page=3,page_size=15, total = 60, items=queues[30:45])
        with patch.object(QueueService, "paginate", return_value=paginated):
            response = client.get(f"{BASE_URL}?page=3&page_size=15")
        assert response.status_code == 200
        data = response.json
        assert data["pagination"]["page_size"] == 15
        assert data["pagination"]["page"] == 3
        assert data["pagination"]["total"] == 60
        assert len(data["items"]) == 15
        assert data["items"] == [t.to_dict() for t in queues[30:45]]

    def test_out_of_page(self, client):
        paginated = make_mock_paginated(page=5,page_size=15, total = 10, items=[])
        with patch.object(QueueService, "paginate", return_value=paginated):
            response = client.get(f"{BASE_URL}?page=5")
        assert response.status_code == 200
        data = response.json
        assert data["pagination"]["page_size"] == 15
        assert data["pagination"]["total"] == 10
        assert data["pagination"]["page"] == 5
        assert len(data["items"]) == 0
        assert data["items"] == []

    def test_invalid_pagination_parameters(self, client):
        with patch.object(QueueService, "paginate", side_effect=MalformatedInputException):
            response = client.get(f"{BASE_URL}?page=abc&page_size=15")
        assert response.status_code == 422

