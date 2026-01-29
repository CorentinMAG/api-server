import pytest
from api import create_app
import os

os.environ["DTR_ENV"] = "TESTING"

@pytest.fixture(scope="session")
def app():
    app = create_app()
    return app

@pytest.fixture(scope="function")
def session(app):
    return app.session