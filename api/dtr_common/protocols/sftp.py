from __future__ import annotations

import re
import time
from pathlib import Path

from dtr_common.exceptions.errors import (
    ConnectionError,
    DownloadError,
    ListError,
    PurgeError,
    RenameError,
    UploadError,
)
from dtr_common.utils import task
from paramiko import AutoAddPolicy, SSHClient

from ..utils import convert_datetime_regex
from .base import BaseProtocol, IFetch


class SFTPProtocol(BaseProtocol):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if self.path:
            self.path = convert_datetime_regex(self.path)
        self.ssh = None

    @task(error=ConnectionError)
    def connect(self) -> None:
        if self.credentials is None:
            raise ConnectionError("No credentials")
        self.ssh = SSHClient()
        self.ssh.set_missing_host_key_policy(AutoAddPolicy())
        self.ssh.connect(
            self.host,
            self.port,
            self.credentials["login"],
            self.credentials["password"].get_secret_value(),
            allow_agent=False,
        )
        self.client = self.ssh.open_sftp()

    @task()
    def disconnect(self) -> None:
        if self.client:
            self.client.close()
        if self.ssh:
            self.ssh.close()

    @task(error=ListError)
    def fetch(self, pattern: str) -> list[IFetch]:
        pattern = convert_datetime_regex(pattern)
        if self.path is None:
            files = self.client.listdir()
        else:
            files = self.client.listdir(self.path)
        files = list(filter(lambda f: re.search(pattern, f), files))
        files = list(map(lambda f: f"{self.path}/{f}" if self.path else f, files))
        stats = [self.client.stat(f) for f in files]

        files = [
            {"filename": f.split("/")[-1], "size": s.st_size / 1e6, "modified_at": s.st_mtime}
            for f, s in zip(files, stats)
        ]
        return files

    def _progress(self, transferred: int, size: float) -> None:
        percent = round((transferred / size) * 100) if size else 100
        if percent % 10 == 0 and self._last_percent != percent:
            self.logger.info("progress file: %d%%", percent)
            self._last_percent = percent

    def _transfer(self, mode: str, src: str, dest: str, size: float) -> None:
        total_size_bytes = size * 1e6  # Convert size from MB to bytes
        self._last_percent = -1

        if mode == "upload":
            self.client.put(src, dest, callback=self._progress)
        elif mode == "download":
            self.client.get(src, dest, callback=self._progress)

    @task(error=UploadError)
    def upload(self, src: str, size: float) -> tuple[float, float]:
        filepath = Path(src)
        original_filename = filepath.name

        tmp_prefix = self.kwargs.get("tmp_prefix") or ""
        final_prefix = self.kwargs.get("final_prefix") or ""

        filename = tmp_prefix + original_filename
        tmp_path = self._build_path(filename)

        # Ensure remote directory hierarchy exists; then work inside it for atomic rename
        if self.path is not None:
            for dir in self.path.strip("/").split("/"):
                if dir not in self.client.listdir():
                    self.client.mkdir(dir)
                self.client.chdir(dir)
            self.client.chdir(None)

        start = time.time()
        self._transfer("upload", src, tmp_path, size)
        end = time.time()

        if final_prefix:
            filename = final_prefix + original_filename
            final_path = self._build_path(filename)
            self.rename(tmp_path, final_path)
        else:
            # if there is a tmp_prefix but no final_prefix,
            # we need to remove the tmp_prefix once the download
            # step is over
            final_path = self._build_path(original_filename)
            self.rename(tmp_path, final_path)

        delta = end - start
        rate = round(size / delta, 2)
        return rate, delta

    @task(error=DownloadError)
    def download(self, filename: str, dest: str, size: float | None = None) -> tuple[float, float, float]:
        filepath = self._build_path(filename)
        if size is None:
            size = round(self.client.stat(filepath).st_size // 1e6, 2)

        start = time.time()
        self._transfer("download", filepath, dest, size)
        end = time.time()
        delta = end - start
        rate = round(size / delta, 2) if delta > 0 else 99999
        return size, rate, delta

    @task(error=RenameError)
    def rename(self, src: str, dest: str) -> None:
        if src != dest:
            self.client.rename(src, dest)

    @task(error=PurgeError)
    def purge(self, filename: str) -> None:
        filepath = self._build_path(filename)
        self.client.remove(filepath)
