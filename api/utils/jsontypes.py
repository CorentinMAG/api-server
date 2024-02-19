from typing import TypedDict, Literal

class CredentialsJson(TypedDict, total = False):
    login: str
    password: str
    type: str
    token: str

class NotificationServerJson(TypedDict, total = False):
    name: str
    type: str
    host: str
    port: int
    timeout: str
    credentials: CredentialsJson

class TargetJson(TypedDict, total = False):
    name: str
    protocol: Literal["FTPS", "SFTP", "S3"]
    host: str
    port: int
    credentials: CredentialsJson

class KafkaServerParametersJson(TypedDict, total = False):
    server: str
    topic: str
    replica: int
    partitions: int

class SrcPolicyJson(TypedDict, total = False):
    target: str
    path: str
    purge: str

class DestPolicyJson(TypedDict, total = False):
    target: str
    path: str

class PeriodicalParametersJson(TypedDict, total = False):
    polling_interval: int

class TransferPolicyJson(TypedDict, total = False):
    name: str
    type: str
    queues: list[str]
    data_type: Literal["file", "directory"]
    notifications: list[KafkaServerParametersJson]
    periodical: PeriodicalParametersJson
    pattern: str
    src: SrcPolicyJson
    dest: DestPolicyJson

class QueueJson(TypedDict, total = False):
    name: str
    max_requests: int
    priority: int

class ConfigurationJson(TypedDict):
    notification_servers: list[NotificationServerJson]
    queues: list[QueueJson]
    targets: list[TargetJson]
    transfer_policies: list[TransferPolicyJson]

class FilterPolicyParams(TypedDict):
    enabled: bool
    type: Literal["periodical", "commanded"]
    dataType: Literal["file", "folder"] 