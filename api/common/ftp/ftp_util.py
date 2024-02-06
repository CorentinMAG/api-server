from __future__ import annotations

import ssl
from .ftps import MYFTPS

def generate_tls_context(certpath: str, check_hostname: bool) -> ssl.SSLContext:
    ctx = ssl.SSLContext()
    ctx.options |= ssl.OP_NO_SSLv2
    ctx.options |= ssl.OP_NO_SSLv3
    ctx.check_hostname = check_hostname
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_verify_locations(cafile=f"{certpath}/ca-bundle.crt")
    return ctx


def connect_ftps(certpath: str, host:str, port: str, user: str, password: str, check_hostname: bool) -> MYFTPS:
    ssl_ctx = generate_tls_context(
        certpath,
        check_hostname
    )
    ftps = MYFTPS(context=ssl_ctx)
    ftps.connect(host, port)
    ftps.login(user, password)
    ftps.prot_p()

    return ftps
