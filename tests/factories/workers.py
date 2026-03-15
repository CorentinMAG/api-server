from faker import Faker
from unittest.mock import Mock

def make_worker(faker: Faker):
    payload = {
        "name": faker.slug(),
        "priority": faker.random_digit_not_null(),
        "worker_timeout": faker.random_digit_not_null() * 10 if faker.boolean() else None,
        "worker_limit": faker.random_digit_not_null() * 10 if faker.boolean() else None
    }

    payload["worker_threshold"] = int(payload["worker_limit"] / faker.random_digit_not_null()) if payload["worker_limit"] is not None else None 
    return payload

def make_workers(number: int = 1):
    workers = [
        make_worker()
        for _ in range(number)
    ]
    return workers

def make_mock_worker(worker, faker: Faker, id: int | None = None):
    t = Mock()
    if id is None:
        id = faker.random_digit()
    t.to_dict.return_value = {"id": id, **worker}
    return t

def make_mock_workers(workers):
    data = []
    for i, worker in enumerate(workers):
        data.append(make_mock_worker(worker, i))
    return data
