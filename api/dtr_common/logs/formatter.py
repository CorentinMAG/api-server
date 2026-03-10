from __future__ import annotations

import json
import logging


class JsonFormatter(logging.Formatter):
    default_msec_format = None
    default_time_format = "%Y-%m-%dT%H:%M:%S"

    def __init__(
        self, ssystem: str, component: str, component_version: str, ssystem_version: str, *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.ssystem = ssystem
        self.ssystem_version = ssystem_version
        self.component = component
        self.component_version = component_version

    def format(self, record):
        data = {
            "message_header": {
                "type": record.type if hasattr(record, "type") else "LOG",
                "timestamp": self.formatTime(record),
                "level": record.levelname,
                "ssystem": self.ssystem,
                "ssystem_version": self.ssystem_version,
                "component": self.component,
                "component_version": self.component_version,
            },
            "message_content": {"content": record.getMessage()},
        }
        if hasattr(record, "message_header"):
            header = record.message_header
            data["message_header"].update(header)

        if hasattr(record, "custom"):
            data["custom"] = record.custom

        if hasattr(record, "task"):
            data["task"] = record.task

        if hasattr(record, "data_rate_megabytes_sec"):
            data["data_rate_megabytes_sec"] = record.data_rate_megabytes_sec
        if hasattr(record, "data_volume_mega_bytes"):
            data["data_volume_mega_bytes"] = record.data_volume_mega_bytes
        if hasattr(record, "satellite"):
            data["satellite"] = record.satellite
        log = json.dumps(data)
        return log
