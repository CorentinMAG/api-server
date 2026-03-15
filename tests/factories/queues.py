from faker import Faker
from unittest.mock import Mock



def make_queues(number: int = 1):
    queues = [
        make_queue()
        for _ in range(number)
    ]
    return queues

def make_mock_queue(queue, faker: Faker, id: int | None = None):
    t = Mock()
    if id is None:
        id = faker.random_digit()
    t.to_dict.return_value = {"id": id, **queue}
    return t

def make_mock_queues(queues):
    data = []
    for i, queue in enumerate(queues):
        data.append(make_mock_queue(queue, i))
    return data
