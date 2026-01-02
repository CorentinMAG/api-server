from __future__ import annotations

import ssl


def generate_tls_context(certpath: str, check_hostname: bool, verify: bool) -> ssl.SSLContext:
    ctx = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
    ctx.options |= ssl.OP_NO_SSLv2
    ctx.options |= ssl.OP_NO_SSLv3
    ctx.check_hostname = check_hostname
    ctx.verify_mode = ssl.CERT_REQUIRED if verify else ssl.CERT_NONE
    ctx.load_verify_locations(cafile=f"{certpath}/ca-bundle.crt")
    return ctx
