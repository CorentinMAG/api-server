from faker import Faker
from unittest.mock import Mock

def make_targets(number: int = 1):
    targets = [
        make_target()
        for _ in range(number)
    ]
    return targets

def make_mock_target(target, faker: Faker, id: int | None = None):
    t = Mock()
    if id is None:
        id = faker.random_digit()
    t.to_dict.return_value = {"id": id, **target}
    return t

def make_mock_targets(targets):
    data = []
    for i, target in enumerate(targets):
        data.append(make_mock_target(target, i))
    return data
