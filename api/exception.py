class AppException(Exception):
    """Base class for all application exceptions"""

    def __init__(self, message: str, status_code: int = 500):
        self._message = message
        self._status_code = status_code
        super().__init__(self.message)

    @property
    def message(self) -> str:
        return self._message

    @property
    def status_code(self) -> int:
        return self._status_code


class MalformatedInputException(AppException):
    def __init__(self, message: str = "malformatted input"):
        super().__init__(message, status_code=422)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class NotConfiguredException(AppException):
    def __init__(self, message: str = "Data Transfer parameters not configured"):
        super().__init__(message, status_code=503)
