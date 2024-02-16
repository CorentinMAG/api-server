import ssl
from ftplib import FTP, FTP_TLS
from socket import socket

from flask import current_app as app

"""
According to vsftpd documentation
the parameter require_ssl_reuse may break
many FTP client (and break ftplib)
The workaround is to use a subclass of FTP_TLS
"""


class MYFTPS(FTP_TLS):
    def ntransfercmd(
        self, cmd: str, rest: int | str | None = None
    ) -> tuple[socket, int]:
        conn, size = FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:  # type: ignore[attr-defined]
            conn = self.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session  # type: ignore[union-attr]
            )
        return conn, size


def generate_tls_context(check_hostname: bool) -> ssl.SSLContext:
    ctx = ssl.SSLContext()
    ctx.options |= ssl.OP_NO_SSLv2
    ctx.options |= ssl.OP_NO_SSLv3
    ctx.check_hostname = check_hostname
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_verify_locations(cafile=f"{app.config['CERT_FOLDER']}/ca-bundle.crt")
    return ctx


def connect_ftps() -> MYFTPS:
    FTP_SERVER = app.config["ftps"]
    ssl_ctx = generate_tls_context(
        FTP_SERVER["check_hostname"],
    )
    ftps = MYFTPS(context=ssl_ctx)
    ftps.connect(FTP_SERVER["host"], FTP_SERVER["port"])
    ftps.login(FTP_SERVER["user"], FTP_SERVER["password"])
    ftps.prot_p()

    if FTP_SERVER.get("subdir"):
        subdirs = FTP_SERVER["subdir"].strip("/").split("/")
        for dir in subdirs:
            ldirs = ftps.nlst()

            ftps.mkd(dir)
            ftps.cwd(dir)
    return ftps
