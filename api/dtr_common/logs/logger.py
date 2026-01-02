import logging

from dtr_common.logs import formatter as fmt

def create_logger(
    name: str, level: str, component_version: str, ssystem: str, ssystem_version: str, format: str = "json"
) -> logging.Logger:
    # the logger name should be the component name
    level = level.upper()
    if level == "DEBUG":
        lvl = logging.DEBUG
    elif level == "INFO":
        lvl = logging.INFO
    elif level == "WARNING":
        lvl = logging.WARNING
    elif level == "ERROR":
        lvl = logging.ERROR
    else:
        raise NameError(f"Unknown logging level: {level}")

    logger = logging.getLogger(name)
    logger.setLevel(lvl)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(lvl)
    formatter = getattr(fmt, f"{format.capitalize()}Formatter")
    stream_handler.setFormatter(formatter(ssystem, name, component_version, ssystem_version))
    logger.addHandler(stream_handler)
    return logger
