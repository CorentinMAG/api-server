from __future__ import annotations
from copy import deepcopy
from typing import cast, Callable, TYPE_CHECKING
import datetime
import math
import re
import shutil
from pathlib import Path
import functools
import uuid

if TYPE_CHECKING:
    from .protocols import BaseProtocol


def choose_chunk_size(size: float) -> tuple[int, int]:
    """
    choose a safe multipart chunk size for s3 uploads
    size is in MB
    constraints:
      mimimum part size: 5MB
      maxmimum part size: 5GB
      maximum number of parts 10 000
    """
    min_chunk = 5 * 1024 * 1024 # 5 MB
    max_parts = 10_000
    max_chunk =  min_chunk * 1024 # 5 GB

    # min_chunk size to stay under max_parts parts
    min_chunk = max(min_chunk, math.ceil(size / max_parts))
    chunk_size = 2 ** math.ceil(math.log2(min_chunk))

    # adjust chunk size for performance
    num_parts = math.ceil(size / chunk_size)
    while num_parts > 1_000 and chunk_size < max_chunk:
        chunk_size *= 2
        num_parts = math.ceil(size / chunk_size)
    
    # cap chunk size to stay under max_chunk_size
    chunk_size = min(chunk_size, max_chunk)

    nb_parts = math.ceil(size / chunk_size)

    # boto3 works with bytes
    chunk_size = chunk_size * 1024 * 1024
    return chunk_size, nb_parts


def parse_params(params: dict[str, str]) -> dict[str, str | int | bool]:
    """
    this function parse query parameters
    """
    new_params = deepcopy(params)
    for key, value in new_params.items():
        if value.lower() in ("true", "false"):
            new_params[key] = True if value.lower() == "true" else False  # type: ignore
        elif value.isdigit():
            new_params[key] = int(value)  # type: ignore
    return cast(dict[str, str | int | bool], new_params)


def convert_datetime_regex(pattern: str) -> str:
    """
    Extract all date pattern matches (%x or %-x, x being a char), make them unique and
    replace all matches by the corresponding date
    """
    now = datetime.datetime.utcnow()
    return now.strftime(pattern)


def parse_storage_value(size: str) -> int:
    """
    input is the size in Gi or Go
    and output is size in Mo
    """
    try:
        value = int(size)
    except ValueError:
        # there is a unit suffix
        # must be Gi or Go
        value = int(re.sub(r"[a-zA-Z]", "", size))
    return round(value * 1e3)

def merge(d1: dict, d2: dict):
    """merge 2 dictionnaries"""
    result = {}
    for k in d1.keys() | d2.keys():
        if k in d1 and k in d2:
            if isinstance(d1[k], dict) and isinstance(d2[k], dict):
                result[k] = merge(d1[k], d2[k])
            else:
                result[k] = d2[k]
        elif k in d1:
            result[k] = d1[k]
        else:
            result[k] = d2[k]
    return result


def clean_directory(dir_path: Path) -> None:
    """
    Clean the specified directory by removing all its contents.
    """
    for x in dir_path.iterdir():
        if x.is_dir():
            shutil.rmtree(x)
        else:
            x.unlink()

def task(error: type[Exception] | None = None):
    def decorator(f: Callable):
        @functools.wraps(f)
        def wrapper(self: BaseProtocol, *args, **kwargs):
            f_name = f.__name__
            logger = self.logger
            _uuid = uuid.uuid4()
            inputs = {}
            outputs = {}

            begin_task = {
                "type": "REPORT",
                "task": {
                    "event": "BEGIN"
                }
            }
            end_task = {
                "type": "REPORT",
                "task": {
                    "event": "END",
                    "status": "OK",
                    "error_code": 0
                }
            }
            error_task = {
                "type": "REPORT",
                "task": {
                    "event": "END",
                    "status": "NOK",
                    "error_code": 1
                }
            }

            if f_name == "download":
                inputs = {
                    "source_url_string": self.path,
                    "filename_string": kwargs["filename"],
                    "target_url_string": kwargs["dest"]
                }
            elif f_name == "upload":
                src_path = Path(kwargs["src"])
                filename = src_path.name
                inputs = {
                    "source_url_string": kwargs["src"],
                    "filename_string": filename,
                    "target_url_string": self.path
                }
            name = f"dtr_worker_transfer_file_{f_name}"
            log = {"begin": f"Beginning of file {f_name}", "end": f"End of file {f_name}", "error": lambda e: f"Error in file {f_name}: {e}"}
            task = {
                "task": {
                    "uid": _uuid.hex,
                    "name": name,
                    "input": inputs,
                    "child_of_task": self.job_uuid.hex
                }
            }
            begin_task = merge(begin_task, task)
            try:
                logger.info(log["begin"], extra = begin_task)
                result = f(self, *args, **kwargs)
            except Exception as e:
                error_task = merge(error_task, task)
                logger.error(log["error"](e), extra = error_task)
                if issubclass(error, Exception):
                    raise error(e)
                else:
                    raise
            else:
                if f_name in ("upload", "download"):
                    outputs = {
                        "task": {
                            "data_volume_mega_bytes": result[0],
                            "data_rate_mega_bytes_sec": result[1]
                        }
                    }
                    end_task = merge(end_task, merge(task, outputs))
                    logger.info(log["end"], extra = end_task)
                    return result + (_uuid,)
                return result, _uuid
        return wrapper
    return decorator
