from api.repositories import DTR_REPOSITORIES, BaseRepository
from typing import TypeVar, Generic, cast


RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)
T = TypeVar("T", bound=BaseRepository)


class BaseService(Generic[RepositoryType]):
    _repository_instances: dict[type[BaseRepository], BaseRepository] = {}

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
            repo_class = self._resolve_repository_class(repo_name)
            if repo_class:
                self._repository = self._get_or_create_repository(repo_class)
            else:
                self._repository = None
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
    def _get_or_create_repository(cls, repo_class: type[T]) -> T:
        if repo_class not in cls._repository_instances:
            cls._repository_instances[repo_class] = repo_class()
        return cast(T, cls._repository_instances[repo_class])

    @staticmethod
    def _resolve_repository_class(repo_name: str) -> RepositoryType | None:
        return DTR_REPOSITORIES.get(repo_name)
