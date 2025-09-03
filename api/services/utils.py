from __future__ import annotations

from functools import wraps
from flask import current_app as app
import time
from ..db import db

def transactional(f):
    """
    Decorator to handle database transactions safely with automatic retry.
    Will commit the transaction if successful, rollback if there's an error.
    Includes automatic retry for connection-related database errors.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            db.session.commit()
            return result
        except Exception as e:
            db.session.rollback()
            raise          
    return decorated_function


def db_retry(total: int = 3, backoff: int = 2):
    """
    Decorator for database operations that need retry without transaction management.
    Useful for read-only operations or when you want manual transaction control.

    Args:
        total: Maximum number of retry attempts
        backoff: Multiplier for exponential backoff
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < total:
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    backoff_delay = backoff * (2 ** (attempts - 1))
                    app.logger.error("Attempt %d/%d (%s)", attempts, total, f.__name__)
                    if attempts == total:
                        raise
                    time.sleep(backoff_delay)
        return wrapper
    return decorator
