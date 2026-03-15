from faker import Faker
from dtr_common.constantes import ServerType

faker = Faker()


@pytest.fixture(
    params=[
        {"credentials": None},
        {"parameters": None},
        {"credentials": None, "parameters": None},
    ]
)
def make_target(**overrides):
    return {
        "name": faker.unique.slug(),
        "protocol": faker.random_element(["HTTP", "S3", "SFTP", "FTPS"]),
        "host": faker.hostname(),
        "port": faker.port_number(),
        "credentials": {
            "login": faker.user_name(),
            "password": faker.password(),
        },
        "parameters": {
            "use_ssl": faker.boolean(),
            "verify": faker.boolean(),
            "http_proxy": faker.url(),
            "https_proxy": faker.url(),
        }
        ** overrides,
    }


def make_queue(**override):
    return {
        "name": faker.unique.slug(),
        "priority": faker.random_int(min=1, max=10),
        "queue_timeout": faker.random_int(min=1, max=60),
        "queue_limit": faker.random_int(min=1, max=60),
        "queue_threshold": faker.random_int(min=1, max=60),
        **override,
    }


def make_server(**overrides):
    return {
        "name": faker.unique.slug(),
        "type": ServerType.KAFKA,
        "host": faker.hostname(),
        "port": faker.port_number(),
        "timeout": faker.random_int(min=1, max=60),
        "credentials": {
            "login": faker.user_name(),
            "password": faker.password(),
        }
        ** overrides,
    }


def make_trigger(**overrides):
    return {
        "name": faker.unique.slug(),
        "polling_interval": faker.random_int(min=1, max=60),
        **overrides,
    }


def make_worker(**overrides):
    return {
        "name": faker.unique.slug(),
        "queues": [faker.slug() for _ in range(faker.random_int(min=1, max=10))],
        **overrides,
    }


def make_parameters(**overrides):
    return {
        "final_prefix": faker.random_letter(),
        "max_retry": faker.random_int(min=1, max=10),
        "mode": "online",
        "only_new_data": faker.boolean(),
        "polling_interval": faker.random_int(min=10, max=80),
        "queue_limit": faker.random_int(min=100, max=600),
        "queue_threshold": faker.random_int(min=100, max=600),
        "queue_timeout": faker.random_int(min=10, max=80),
        "retry_delay": faker.random_int(min=10, max=80),
        "tmp_prefix": faker.random_letter(),
        "transfer_requests_history": faker.random_int(min=1, max=31),
        "transfer_timeout": faker.random_int(min=10, max=200),
        **overrides,
    }
