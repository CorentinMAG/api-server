from __future__ import annotations
from api.repositories import DTR_REPOSITORIES, BaseRepository
from typing import TypeVar, Generic, get_type_hints, cast, ClassVar


RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)
T = TypeVar("T", bound=BaseRepository)
S = TypeVar("S")

class BaseService(Generic[RepositoryType]):
    _repository_instances: ClassVar[dict[str, BaseRepository]] = {}
    _service_instances: ClassVar[dict[type, BaseService]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        service_name = cls.__name__
        cls._repository_name = (
            service_name.replace("Service", "Repository") 
            if service_name.endswith("Service") 
            else None
        )

    def __init__(self):
        repo_name = getattr(self.__class__, "_repository_name", None)
        self._repository = self._get_or_create_repository(repo_name) if repo_name else None

        try:
            hints = get_type_hints(self.__class__)
        except Exception:
            hints = self.__class__.__annotations__
        
        for attr_name, attr_type in hints.items():
            if (isinstance(attr_type, type) and issubclass(attr_type, BaseService) and attr_type is not BaseService):
                setattr(self, attr_name, self._get_or_create_service(attr_type))

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
    
    @classmethod
    def _get_or_create_service(cls, service_class: type[S]) -> S:
        if service_class not in cls._service_instances:
            cls._service_instances[service_class] = service_class()
        return cast(S, cls._service_instances[service_class])

