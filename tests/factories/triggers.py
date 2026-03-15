from faker import Faker
from unittest.mock import Mock

def make_trigger(faker: Faker, **overrides):
    payload = {
        "name": faker.slug(),
        "polling_interval": faker.random_digit_not_null() * 10 if faker.boolean() else None
        **overrides
    }
    return payload

def make_triggers(number: int = 1):
    triggers = [
        make_trigger()
        for _ in range(number)
    ]
    return triggers

def make_mock_trigger(trigger: dict, faker: Faker, id: int | None = None):
    t = Mock()
    if id is None:
        id = faker.random_digit()
    t.to_dict.return_value = {"id": id, **trigger}
    return t

def make_mock_triggers(triggers: list[dict]):
    data = []
    for i, trigger in enumerate(triggers):
        data.append(make_mock_trigger(trigger, i))
    return data
