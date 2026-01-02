class ProtocolError(Exception):
    pass


class ConnectionError(ProtocolError):
    pass


class UploadError(ProtocolError):
    pass


class DownloadError(ProtocolError):
    pass


class ListError(ProtocolError):
    pass


class PurgeError(ProtocolError):
    pass


class RenameError(ProtocolError):
    pass


class RetryError(ProtocolError):
    pass
