import pytest
from api.models import Target, Credentials

class TestTargetModel:
    """Test"""

    def test_create_target(self, session):
        target = Target(
            name = "ftps1",
            host="10.8.203.21",
            port=990,
            credentials = Credentials(
                login="ftpuser",
                password="changeme"
            )
        )
        session.add(target)
        session.commit()
        assert target.id is not None