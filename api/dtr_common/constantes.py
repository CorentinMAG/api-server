from enum import Enum


class Protocol(Enum):
    FTPS = "FTPS"
    SFTP = "SFTP"
    S3 = "S3"
    HTTP = "HTTP"


class State(Enum):
    QUEUED = "queued"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    CANCELLED = "cancelled"
    IN_PROGRESS = "in_progress"


class SubState(Enum):
    NOTIFY = "notify"
    NOTIFIED = "notified"


class Mode(Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class Type(Enum):
    PERIODICAL = "periodical"
    COMMANDED = "commanded"


class ServerType(Enum):
    KAFKA = "kafka"
