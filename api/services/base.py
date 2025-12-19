from typing import Generic, TypeVar

RepositoryType = TypeVar("RepositoryType")

class BaseService(Generic[RepositoryType]):
    """base service with common dependencies"""
    def __init__(self, repository: RepositoryType) -> None:
        self._repository = repository

    @property
    def repository(self) -> RepositoryType:
        return self._repository
