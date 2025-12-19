class AppException(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class AppGlobalParametersError(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=404)

class OfflineError(AppGlobalParametersError):
    def __init__(self, message: str = "Application in offline mode"):
        super().__init__(message)

class NotConfiguredError(AppGlobalParametersError):
    def __init__(self, message: str = "Application not configured"):
        super().__init__(message)
