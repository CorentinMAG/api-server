from __future__ import annotations

import logging
import time
from typing import Literal, cast

import requests

from .exceptions.errors import RetryError


def backoff_delay(factor: int, attempt: int) -> int:
    return factor * (2 ** (attempt - 1))


def retry_database_operation(
    operation_func,
    logger: logging.Logger,
    total: int = 5,
    backoff_factor: int = 2,
    initial_delay: int = 1,
    max_delay: int = 60,
    *args,
    **kwargs,
):
    """
    Retry a database operation with exponential backoff for connection issues.

    Args:
        operation_func: The database operation function to retry
        logger: Logger instance for error reporting
        total: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay between retries
        *args, **kwargs: Arguments to pass to operation_func

    Returns:
        Result of operation_func if successful

    Raises:
        RetryError: If all retries are exhausted
    """
    from sqlalchemy.exc import (
        DatabaseError,
        DisconnectionError,
        OperationalError,
        TimeoutError,
    )

    for attempt in range(total):
        try:
            return operation_func(*args, **kwargs)
        except (OperationalError, DisconnectionError, TimeoutError, DatabaseError) as e:
            if attempt == total - 1:  # Last attempt
                logger.error(f"Database operation failed after {total} attempts: {str(e)}")
                raise RetryError(f"Database operation failed after {total} attempts: {str(e)}")

            # Calculate delay with exponential backoff
            delay = min(initial_delay * (backoff_factor**attempt), max_delay)
            logger.warning(
                f"Database operation failed (attempt {attempt + 1}/{total}): {str(e)}. "
                f"Retrying in {delay} seconds..."
            )
            time.sleep(delay)
        except Exception as e:
            # For non-connection related errors, don't retry
            logger.error(f"Non-retryable database error: {str(e)}")
            raise


def retry_request(
    url: str,
    logger: logging.Logger,
    method: Literal["POST", "PUT", "DELETE", "GET"] = "GET",
    total: int = 5,
    timeout: int = 10,
    backoff_factor: int = 1,
    status_forcelist: list[int] = [500, 502, 503, 504],
    **kwargs,
) -> requests.Response:
    for attempt in range(total):
        try:
            response = cast(
                requests.Response,
                getattr(requests, method.lower())(url, timeout=timeout, **kwargs),
            )
            if response.status_code in status_forcelist:
                delay = backoff_delay(backoff_factor, attempt)
                logger.info("retrying request (%s, %s) in %ds", method, url, delay)
                time.sleep(delay)
                continue
            response.raise_for_status()  # raise an HTTPError if we made a bad request (4xx or 5xx)
            return response
        except Exception as e:
            error_name = e.__class__.__name__
            delay = backoff_delay(backoff_factor, attempt)
            logger.error(
                "Error during API call: %s (%s): %s will retry in %ds",
                error_name,
                url,
                e,
                delay,
            )
            time.sleep(delay)
            continue
    logger.error(f"unable to get a response ({method}, {url}) after {total} attempts")
    raise RetryError(f"unable to get a response ({method}, {url}) after {total} attempts")
