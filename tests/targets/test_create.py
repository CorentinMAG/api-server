
import pytest
from unittest.mock import patch
from tests.factories.targets import (
    make_target,
    make_mock_target
)
from sqlalchemy.exc import IntegrityError
from api.services import TargetService

BASE_URL = "/api/v1/targets"

class TestCreateTarget:

    @pytest.mark.parametrize("params", [
        (
            {
                "with_credentials": True, 
                "with_parameters": True
            }
        ),
        (
            {
                "with_credentials": False, 
                "with_parameters": True
            }
        ),
        (
            {
                "with_credentials": True,
                "with_parameters": False
            }
        ),
        (
            {
                "with_parameters": False,
                "with_credentials": False
            }
        )])
    def test_create_target(self, client, params):
        payload = make_target(**params)
        target = make_mock_target(payload)

        with patch.object(TargetService, "create", return_value=target):
            response = client.post(BASE_URL, json = payload)
        assert response.status_code == 201
        assert response.json == target.to_dict()

    @pytest.mark.parametrize("missing_field", ["name", "protocol", "host", "port"])
    def test_create_with_missing_field(self, client, missing_field):
        payload = make_target()
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
        payload = make_target()

        with patch.object(TargetService, "create", side_effect=error):
            response = client.post(BASE_URL, json=payload)
        assert response.status_code == status_code
