from __future__ import annotations


class AppException(Exception):
    """Base class for all application exceptions."""

    def __init__(self, message: str, status_code: int):
        self._message = message
        self._status_code = status_code
        super().__init__(message)

    @property
    def message(self) -> str:
        """Get the exception message."""
        return self._message

    @property
    def status_code(self) -> int:
        """Get the HTTP status code associated with the exception."""
        return self._status_code


class NotFoundException(AppException):
    """Exception raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)
