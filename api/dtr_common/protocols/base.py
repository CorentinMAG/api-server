from __future__ import annotations

from abc import ABC, abstractmethod
from logging import Logger
from pathlib import Path
from typing import TypedDict
from uuid import UUID


class IFetch(TypedDict):
    filename: str
    size: float  # in Mo
    modified_at: int  # timestamp


class BaseProtocol(ABC):
    def __init__(self, logger: Logger, target: dict, path: str | None = None, **kwargs) -> None:
        self.host = target["host"]
        self.port = target["port"]
        self.protocol = target["protocol"]
        self.credentials = target["credentials"]
        self.parameters = target["parameters"]
        self.path = path
        self.target = target
        self.client: None | any = None
        self.logger = logger
        self.kwargs = kwargs
        self._job_uuid: UUID | None = None

    def __enter__(self) -> BaseProtocol:
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()

    @property
    def job_uuid(self) -> UUID | None:
        return self._job_uuid

    @job_uuid.setter
    def job_uuid(self, uuid: UUID) -> None:
        self._job_uuid = uuid

    def _build_path(self, filename: str) -> str:
        """Build a full path by combining self.path and filename if path exists"""
        return str(Path(self.path) / filename) if self.path else filename

    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def fetch(self, pattern: str) -> list[IFetch]:
        pass

    @abstractmethod
    def upload(self, src: str, size: float) -> tuple[float, float]:
        pass

    @abstractmethod
    def download(self, filename: str, dest: str, size: float | None = None) -> tuple[float, float, float]:
        pass

    @abstractmethod
    def purge(self, filename: str) -> None:
        pass

    @abstractmethod
    def rename(self, src: str, dest: str) -> None:
        pass
