import os
import pytest
from api import create_app

os.environ["DTR_ENV"] = "testing"

@pytest.fixture
def app():
    """Create a test app instance."""
    app = create_app()

    yield app
    return app

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def db_session(app):
    with app.app_context():
        session = app.session

        yield session

        session.rollback()
        session.close()