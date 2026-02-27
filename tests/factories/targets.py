from faker import Faker
from unittest.mock import Mock

fake = Faker()

def make_parameters(**overrides):
    return {
        "use_ssl": fake.boolean(),
        "verify": fake.boolean(),
        "http_proxy": fake.url() if fake.boolean() else None,
        "https_proxy": fake.url() if fake.boolean() else None,
        **overrides
    }

def make_credentials(**overrides):
    return {
        "login": fake.user_name(),
        "password": fake.password(),
        **overrides
    }

def make_target(with_credentials=True, with_parameters=True, **overrides):
    payload = {
        "name": fake.slug(),
        "protocol": fake.random_element(["HTTP", "S3", "SFTP", "FTPS"]),
        "host": fake.hostname(),
        "port": fake.port_number(),
        **overrides
    }

    if with_credentials:
        payload["credentials"] = make_credentials()
    if with_parameters:
        payload["parameters"] = make_parameters()
    return payload

def make_targets(number: int = 1):
    targets = [
        make_target(
            with_credentials=fake.boolean(), 
            with_parameters=fake.boolean())
        for i in range(number)
    ]
    return targets

def make_mock_target(target, id: int | None = None):
    t = Mock()
    if id is None:
        id = fake.random_digit()
    t.to_dict.return_value = {"id": id, **target}
    return t

def make_mock_targets(targets):
    data = []
    for i, target in enumerate(targets):
        data.append(make_mock_target(target, i))
    return data

def make_mock_paginated(page: int, page_size: int, total: int, items: list):
    paginated = Mock()

    pagination = Mock()

    pagination.model_dump.return_value = {
        "page": page,
        "page_size": page_size,
        "total": total
    }

    paginated.pagination = pagination
    paginated.items = items
    return paginated
