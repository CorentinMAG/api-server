from api.repositories import DTR_REPOSITORIES, BaseRepository
from typing import TypeVar, Generic


RepositoryType = TypeVar("RepositoryType")

class BaseService(Generic[RepositoryType]):
    _repository_instances: dict[str, BaseRepository] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        service_name = cls.__name__
        if service_name.endswith("Service"):
            cls._repository_name = service_name.replace("Service", "Repository")
        else:
            cls._repository_name = None

    def __init__(self):
        repo_name = getattr(self.__class__, "_repository_name", None)
        if repo_name:
            self._repository = self._get_or_create_repository(repo_name)
        else:
            self._repository = None

    @property
    def repository(self) -> RepositoryType:
        if self._repository is None:
            raise AttributeError(f"No repository found for {self.__class__.__name__}")
        return self._repository

    def commit(self):
        if self._repository is not None:
            self._repository.session.commit()

    @classmethod
    def _get_or_create_repository(cls, repo_name: str) -> RepositoryType:
        if repo_name not in cls._repository_instances:
            repo_class = cls._resolve_repository_class(repo_name)
            if not repo_class:
                raise ValueError(f"Repository class '{repo_name}' not found.")
            cls._repository_instances[repo_name] = repo_class()
        return cls._repository_instances[repo_name]

    @staticmethod
    def _resolve_repository_class(repo_name: str) -> RepositoryType | None:
        return DTR_REPOSITORIES.get(repo_name)

