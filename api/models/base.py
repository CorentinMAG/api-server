from abc import ABC, abstractmethod

class BaseModel(ABC):

    @abstractmethod
    def upsert(self) -> int:
        """
        implement this method to create / update a model
        """

    @abstractmethod
    def delete(self) -> None:
        """
        implement this method to delete a model instance
        """