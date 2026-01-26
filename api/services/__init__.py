from .base import BaseService


DTR_SERVICES = {cls.__name__: cls for cls in BaseService.__subclasses__()}
