import logging
import json

class JsonFormatter(logging.Formatter):
    def __init__(self, ssystem: str, component: str, version: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.ssystem = ssystem
        self.component = component
        self.version = version

    def format(self, record):
        log_data = {
            "Header": {
                "type": "LOG",
                "timestamp": self.formatTime(record),
                "level": record.levelname,
                "ssystem": self.ssystem,
                "component": self.component,
                "component_version": self.version
            },
            "Message": record.getMessage()
        }
        return json.dumps(log_data)