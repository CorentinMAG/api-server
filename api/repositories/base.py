from abc import ABC, abstractmethod

class BaseRepository(ABC):
    @abstractmethod
    def add(self, entity) -> int:
        pass

    @abstractmethod
    def remove(self, entity) -> None:
        pass

    @abstractmethod
    def get_by_id(self, id: int):
        pass

    @abstractmethod
    def get_all(self):
        pass

    def __getitem__(self, idx: int):
        return self.get_by_id(idx)

