from __future__ import annotations

import datetime
import os
import re
import time
from ftplib import FTP
from pathlib import Path

from dtr_common.exceptions.errors import (
    ConnectionError,
    DownloadError,
    ListError,
    PurgeError,
    RenameError,
    UploadError,
)

from ..ftp.ftp_util import generate_tls_context
from ..ftp.ftps import MYFTPS
from ..utils import convert_datetime_regex, task
from .base import BaseProtocol, IFetch


class FTPSProtocol(BaseProtocol):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if self.path:
            self.path = convert_datetime_regex(self.path)

    @task(error=ConnectionError)
    def connect(self, check_hostname: bool = False) -> None:
        if self.parameters["use_ssl"]:
            cert_path = os.environ["DTR_CERT_PATH"]
            ctx = generate_tls_context(
                certpath=cert_path, check_hostname=check_hostname, verify=self.parameters["verify"]
            )
            self.client = MYFTPS(context=ctx)
        else:
            self.client = FTP()
        self.client.connect(self.host, self.port)
        if self.credentials is not None:
            self.client.login(self.credentials["login"], self.credentials["password"].get_secret_value())
        else:
            raise ValueError("login and password not set")

        if self.parameters["use_ssl"]:
            self.client.prot_p()

    @task()
    def disconnect(self) -> None:
        if self.client:
            self.client.close()

    @task(error=ListError)
    def fetch(self, pattern: str) -> list[IFetch]:
        pattern = convert_datetime_regex(pattern)
        if self.path is None:
            files = self.client.nlst()
        else:
            files = self.client.nlst(self.path)
        files = list(filter(lambda f: re.search(pattern, f), files))

        files = list(
            map(
                lambda f: {
                    "filename": f.split("/")[-1],
                    "size": self.client.size(f) / 1e6,  # we convert the size from octet to Mo
                    "modified_at": datetime.datetime.strptime(
                        self.client.sendcmd(f"MDTM {f}")[4:], "%Y%m%d%H%M%S"
                    ).timestamp(),
                },
                files,
            )
        )

        return files

    @task(error=UploadError)
    def upload(self, src: str, size: float) -> tuple[float, float]:
        filepath = Path(src)
        original_filename = filepath.name

        tmp_prefix = self.kwargs.get("tmp_prefix") or ""
        final_prefix = self.kwargs.get("final_prefix") or ""

        filename = tmp_prefix + original_filename
        tmp_path = self._build_path(filename)

        if self.path is not None:
            # if the file must be uploaded to the FTPS server
            # at a certain path, we need to move the session
            # to the current path before uploading
            for dir in self.path.strip("/").split("/"):
                if dir not in self.client.nlst():
                    self.client.mkd(dir)
                self.client.cwd(dir)
            self.client.cwd("/")

        start = time.time()
        self._transfer("rb", src, tmp_path, size)
        end = time.time()

        if final_prefix:
            filename = final_prefix + original_filename
            final_path = self._build_path(filename)
            self.rename(tmp_path, final_path)
        else:
            final_path = self._build_path(original_filename)
            self.rename(tmp_path, final_path)

        delta = end - start
        rate = round(size / delta, 2)  # in MB / s
        return rate, delta

    def _transfer(self, mode: str, src: str, dest: str, size: float) -> None:
        total_size_bytes = size * 1e6
        downloaded_size = 0
        last_percent = 0

        if mode == "wb":  # Download
            with open(dest, mode) as f:

                def handle_chunk(chunk: int):
                    nonlocal downloaded_size
                    nonlocal last_percent
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if total_size_bytes > 0:
                        percent = round((downloaded_size / total_size_bytes) * 100)
                    else:
                        percent = 100
                    if percent % 10 == 0 and last_percent != percent:
                        self.logger.debug("downloading file %d%%", percent)
                        last_percent = percent

                self.client.retrbinary(f"RETR {src}", handle_chunk)
        elif mode == "rb":  # Upload
            with open(src, mode) as f:

                def handle_chunk(chunk: int) -> None:
                    nonlocal downloaded_size
                    nonlocal last_percent
                    downloaded_size += len(chunk)
                    percent = round((downloaded_size / total_size_bytes) * 100)
                    if percent % 10 == 0 and last_percent != percent:
                        self.logger.info("uploading file: %d%%", percent)
                        last_percent = percent

                self.client.storbinary(f"STOR {dest}", f, callback=handle_chunk)

    @task(error=DownloadError)
    def download(self, filename: str, dest: str, size: float | None = None) -> tuple[float, float, float]:
        filepath = self._build_path(filename)
        if size is None:
            size = round(self.client.size(filepath) // 1e6, 2)

        start = time.time()
        self._transfer("wb", filepath, dest, size)
        end = time.time()
        delta = end - start
        rate = round(size / delta, 2)  # in Mb / s
        return size, rate, delta

    @task(error=RenameError)
    def rename(self, src: str, dest: str) -> None:
        if src != dest:
            self.client.rename(src, dest)

    @task(error=PurgeError)
    def purge(self, filename: str) -> None:
        filepath = self._build_path(filename)
        self.client.delete(filepath)
