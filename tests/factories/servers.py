from faker import Faker
from unittest.mock import Mock
from dtr_common.constantes import ServerType


def make_server(faker: Faker, with_credentials: bool = True, **overrides):
    def _make_credentials(**overrides):
        return {
            "login": faker.user_name(),
            "password": faker.password(),
            **overrides
        }
    
    payload = {
        "name": faker.slug(),
        "type": ServerType.KAFKA,
        "host": faker.hostname(),
        "port": faker.port_number(),
        "timeout": faker.random_number(digits=2, fix_len=2),
        **overrides
    }
    if with_credentials or faker.boolean():
        payload["credentials"] = _make_credentials()
    return payload

def make_servers(faker: Faker, number: int = 1):
    servers = [
        make_server(with_credentials=faker.boolean())
        for _ in range(number)
    ]
    return servers

def make_mock_server(server, faker: Faker, id: int | None = None):
    t = Mock()
    if id is None:
        id = faker.random_digit()
    t.to_dict.return_value = {"id": id, **server}
    return t

def make_mock_servers(servers):
    data = []
    for i, server in enumerate(servers):
        data.append(make_mock_server(server, i))
    return data
