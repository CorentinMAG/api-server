import pytest
from api import create_app
import os

os.environ["DTR_ENV"] = "TESTING"


@pytest.fixture()
def app():
    app = create_app()
    return app


@pytest.fixture
def client(app):
    """Create a test client for the app"""
    return app.test_client()


@pytest.fixture()
def session(app):
    session = app.session

    yield session

    session.rollback()
    session.close()
