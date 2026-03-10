from __future__ import annotations

import datetime
import time
from pathlib import Path

import requests
from dtr_common.exceptions.errors import (
    ConnectionError,
    DownloadError,
    ListError,
    PurgeError,
    RenameError,
    UploadError,
)
from dtr_common.utils import task
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from ..utils import convert_datetime_regex
from .base import BaseProtocol, IFetch


class HTTPProtocol(BaseProtocol):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if self.path:
            self.path = convert_datetime_regex(self.path)
        protocol = "https" if self.parameters["use_ssl"] else "http"
        self.root_url = f"{protocol}://{self.host}:{self.port}"
        # Default timeouts (connect, read) in seconds
        self.timeouts = self.parameters.get("timeouts", (5, 30))
        # Default chunk size for streaming (8MB)
        self.chunk_size = self.parameters.get("chunk_size", 8 * 1024 * 1024)

    @task(error=ConnectionError)
    def connect(self) -> None:
        self.client = requests.Session()

        # Configure retries
        retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.client.mount("http://", adapter)
        self.client.mount("https://", adapter)

        if self.credentials:
            self.client.auth = (self.credentials["login"], self.credentials["password"].get_secret_value())
        self.client.verify = self.parameters["verify"] if self.parameters["use_ssl"] else False

    @task()
    def disconnect(self) -> None:
        if self.client:
            self.client.close()

    @task(error=ListError)
    def fetch(self, pattern: str) -> list[IFetch]:
        pattern = convert_datetime_regex(pattern)
        url = f"{self.root_url}/{self._build_path(pattern)}"

        response = self.client.get(url, timeout=self.timeouts)
        response.raise_for_status()  # Raise exception for 4xx/5xx status codes

        if response.status_code == 200:
            filename = pattern
            size = float(response.headers.get("Content-length", 0)) / 1e6
            modified_at = datetime.datetime.strptime(
                response.headers.get(
                    "Last-Modified", datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
                ),
                "%a, %d %b %Y %H:%M:%S GMT",
            ).timestamp()
            return [{"filename": filename, "size": size, "modified_at": modified_at}]
        return []

    @task(error=DownloadError)
    def download(self, filename: str, dest: str, size: float | None = None) -> tuple[float, float, float]:
        url = f"{self.root_url}/{self._build_path(filename)}"
        start = time.time()
        downloaded_bytes = 0
        last_percent = 0

        with self.client.get(url, stream=True, timeout=self.timeouts) as response:
            response.raise_for_status()

            total_size_bytes = float(response.headers.get("Content-length", 0))
            if size is None:
                size = total_size_bytes / 1e6  # Convert to MB if not provided
            elif total_size_bytes == 0:  # If size was provided but Content-length is 0, use provided size
                total_size_bytes = size * 1e6

            with open(dest, "wb") as f:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_bytes += len(chunk)
                        percent = round((downloaded_bytes / total_size_bytes) * 100)
                        if percent % 10 == 0 and last_percent != percent:
                            self.logger.debug("downloading file: %d%%", percent)
                            last_percent = percent
        end = time.time()
        delta = end - start
        rate = round(size / delta, 2) if delta > 0 else 0
        return size, rate, delta

    @task(error=UploadError)
    def upload(self, src: str, size: float) -> tuple[float, float]:
        filepath = Path(src)
        filename = filepath.name
        url = f"{self.root_url}/{self._build_path(filename)}"

        start = time.time()
        with open(filepath, "rb") as f:
            self.client.post(url, files={"file": f})
        end = time.time()
        delta = end - start
        rate = round(size / delta, 2) if delta > 0 else 0

        return rate, delta

    @task(error=RenameError)
    def rename(self, src: str, dest: str) -> None:
        raise RenameError("HTTPS, cannot rename file")

    @task(error=PurgeError)
    def purge(self, filename: str) -> None:
        url = f"{self.root_url}/{self._build_path(filename)}"
        response = self.client.delete(url, timeout=self.timeouts)
        response.raise_for_status()
