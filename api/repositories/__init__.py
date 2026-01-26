from .base import BaseRepository

DTR_REPOSITORIES = {cls.__name__: cls for cls in BaseRepository.__subclasses__()}
