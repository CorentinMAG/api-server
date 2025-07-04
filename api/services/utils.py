from __future__ import annotations

import logging
from functools import wraps

from dtr_common.exceptions.errors import RetryError
from dtr_common.retry import retry_database_operation
from flask import current_app as app
from sqlalchemy.exc import SQLAlchemyError

from ..db import db


def _get_logger():
    """Get logger with fallback for test environments."""
    try:
        return app.logger
    except RuntimeError:
        # In test environment without Flask context
        return logging.getLogger(__name__)


def transactional(f):
    """
    Decorator to handle database transactions safely with automatic retry.
    Will commit the transaction if successful, rollback if there's an error.
    Includes automatic retry for connection-related database errors.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        def _execute_with_transaction():
            """Inner function that executes the wrapped function with transaction management."""
            try:
                result = f(*args, **kwargs)
                # Check if we're in a Flask application context
                try:
                    db.session.commit()
                except RuntimeError as e:
                    if "Working outside of application context" in str(e):
                        # In test environment without Flask context, skip transaction management
                        pass
                    else:
                        raise
                return result
            except Exception as e:
                try:
                    db.session.rollback()
                    logger = _get_logger()
                    logger.error(f"Transaction failed: {str(e)}", exc_info=True)
                except RuntimeError as context_error:
                    if "Working outside of application context" in str(context_error):
                        # In test environment without Flask context, skip rollback and logging
                        pass
                    else:
                        raise
                raise SQLAlchemyError(f"Database transaction failed: {str(e)}")

        # Use the retry mechanism for database operations
        try:
            return retry_database_operation(
                _execute_with_transaction,
                logger=_get_logger(),
                total=3,  # Reduced retries for API responsiveness
                backoff_factor=2,
                initial_delay=1,
                max_delay=10  # Reduced max delay for API responsiveness
            )
        except RetryError as e:
            # After all retries failed, log and re-raise as SQLAlchemyError
            logger = _get_logger()
            logger.error(f"Database operation failed after all retries: {str(e)}")
            raise SQLAlchemyError(f"Database operation failed after retries: {str(e)}")

    return decorated_function


def db_retry(total: int = 3, backoff_factor: int = 2, initial_delay: int = 1, max_delay: int = 10):
    """
    Decorator for database operations that need retry without transaction management.
    Useful for read-only operations or when you want manual transaction control.

    Args:
        total: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay between retries
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Define a wrapper function that will be called by retry_database_operation
            def _execute_operation():
                return f(*args, **kwargs)

            try:
                return retry_database_operation(
                    _execute_operation,
                    logger=_get_logger(),
                    total=total,
                    backoff_factor=backoff_factor,
                    initial_delay=initial_delay,
                    max_delay=max_delay
                )
            except RetryError as e:
                logger = _get_logger()
                logger.error(f"Database operation failed after all retries: {str(e)}")
                raise SQLAlchemyError(f"Database operation failed after retries: {str(e)}")

        return decorated_function
    return decorator
