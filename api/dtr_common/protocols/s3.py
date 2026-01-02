from .base import BaseProtocol, IFetch
import boto3
import re
from dtr_common.exceptions.errors import ListError, ConnectionError, UploadError, DownloadError, PurgeError
from ..utils import convert_datetime_regex
from dtr_common.utils import task, choose_chunk_size
from pathlib import Path
import time
from boto3.s3.transfer import TransferConfig, S3Transfer
import logging

class ProgressPercentage:
    def __init__(self, logger: logging.Logger, mode: str, filename: str, size: float):
        self._filename = filename
        self._size = size
        self._downloaded_size = 0
        self._lock = None
        self._last_percent = 0
        self._logger = logger
        self._mode = mode

    def __call__(self, bytes_amount) -> None:
        self._downloaded_size += bytes_amount
        if self._size > 0:
            percent = round((self._downloaded_size / self._size) * 100)
        else:
            percent = 100
        if percent % 10 == 0 and self._last_percent != percent:
            if self._mode == "wb":
                self._logger.info("downloading file: %d%%", percent)
            elif self._mode == "rb":
                self._logger.info("uploading file: %d%%", percent)



class S3Protocol(BaseProtocol):
    def __init__(self, bucket: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.bucket = bucket
        if self.path:
            self.path = convert_datetime_regex(self.path)

    @task(error=ConnectionError)
    def connect(self) -> None:
        if self.credentials is None:
            raise ConnectionError("No credentials provided")

        protocol = "https" if self.parameters["use_ssl"] else "http"
        verify = self.parameters["verify"]
        self.client = boto3.client(
            "s3",
            aws_access_key_id=self.credentials["login"],
            aws_secret_access_key=self.credentials["password"].get_secret_value(),
            endpoint_url=f"{protocol}://{self.host}:{self.port}",
            verify=verify,
        )
        # test if credentials are correct
        self.client.list_buckets()

    def disconnect(self) -> None:
        if self.client:
            self.client.close()

    @task(error=ListError)
    def fetch(self, pattern: str) -> list[IFetch]:
        pattern = convert_datetime_regex(pattern)
        if self.path is None:
            metadata = self.client.list_objects(Bucket=self.bucket, Delimiter="/")
        else:
            metadata = self.client.list_objects(Bucket=self.bucket, Prefix=f"{self.path}/", Delimiter="/")

        if metadata.get("Contents", None) is not None:
            files = list(filter(lambda m: re.search(pattern, m["Key"]), metadata["Contents"]))
            files = list(
                map(
                    lambda m: {
                        "filename": m["Key"].split("/")[-1],
                        "size": m["Size"] / 1e6, # in MB
                        "modified_at": m["LastModified"].timestamp(),
                    },
                    files,
                )
            )
            return files
        return []

    def _transfer(self, mode: str, src: str, dest: str, size: float) -> None:
        progress = ProgressPercentage(self.logger, mode, src, size)
        chunk_size, _ = choose_chunk_size(size)
        config = TransferConfig(
            max_concurrency=5, 
            use_threads=True,
            multipart_threshold=5*1024*1024, # Force multipart for anything over 5 MB
            multipart_chunksize=chunk_size
            )
        transfer = S3Transfer(self.client, config)

        if mode == "upload":
            transfer.upload_file(src, self.bucket, dest, callback=progress)
        elif mode == "download":
            transfer.download_file(self.bucket, src, dest, callback=progress)

    @task(error=UploadError)
    def upload(self, src: str, size: float) -> tuple[float, float]:
        # when we upload to a S3 bucket
        # tmp_prefix can't be used
        filepath = Path(src)
        filename = filepath.name

        final_prefix = self.kwargs.get("final_prefix")
        filename = final_prefix + filename if final_prefix is not None else filename

        dest = self._build_path(filename)

        start = time.time()
        # Delegate to _transfer which handles progress tracking
        self._transfer("upload", src, dest, size)
        end = time.time()

        delta = end - start
        rate = round(size / delta, 2)
        return rate, delta

    @task(error=DownloadError)
    def download(self, filename: str, dest: str, size: float | None = None) -> tuple[float, float, float]:
        filepath = self._build_path(filename)
        if size is None:
            metadata = self.client.head_object(Bucket=self.bucket, Key=filepath)
            size = round(metadata["ContentLength"] // 1e6, 2)

        start = time.time()
        self._transfer("download", filepath, dest, size)
        end = time.time()
        delta = end - start
        rate = round(size / delta, 2)
        return size, rate, delta

    def rename(self, src: str, dest: str) -> None:
        """
        with s3 protocol we don't need the
        rename functionality
        """

    @task(error=PurgeError)
    def purge(self, filename: str) -> None:
        key = self._build_path(filename)
        self.client.delete_object(Bucket=self.bucket, Key=key)
