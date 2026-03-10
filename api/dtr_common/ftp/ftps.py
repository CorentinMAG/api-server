from __future__ import annotations

import ssl
from ftplib import FTP, FTP_TLS
from socket import socket

"""
According to vsftpd documentation
the parameter require_ssl_reuse may break
many FTP client (and break ftplib)
The workaround is to use a subclass of FTP_TLS
"""


class MYFTPS(FTP_TLS):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sock = None

    @property
    def sock(self):
        """Return the socket."""
        return self._sock

    @sock.setter
    def sock(self, value):
        """When modifying the socket, ensure that it is ssl wrapped."""
        if value is not None and not isinstance(value, ssl.SSLSocket):
            value = self.context.wrap_socket(value, server_hostname=self.host)
        self._sock = value

    def ntransfercmd(self, cmd: str, rest: int | str | None = None) -> tuple[socket, int]:
        conn, size = FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:  # type: ignore[attr-defined]
            conn = self.context.wrap_socket(
                conn,
                server_hostname=self.host,
                session=self.sock.session,
            )
        return conn, size
