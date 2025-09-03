"""
Abstract base repository providing common database operations.

This module implements the repository pattern with dependency injection
to abstract database access and make services testable.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, Type, TypeVar

from dtr_common.exceptions.errors import RetryError
from dtr_common.retry import retry_database_operation
from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# Generic type for model classes
T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository with common CRUD operations."""

    def __init__(self, model_class: Type[T], db_session: Session):
        """
        Initialize repository with model class and database session.

        Args:
            model_class: SQLAlchemy model class
            db_session: Database session for operations
        """
        self.model_class = model_class
        self.db_session = db_session
        self.logger = logging.getLogger(self.__class__.__name__)

    def _execute_with_retry(self, operation_func, *args, **kwargs):
        """Execute a database operation with retry logic for connection issues."""
        try:
            return retry_database_operation(
                operation_func,
                logger=self.logger,
                total=3,
                backoff_factor=2,
                initial_delay=1,
                max_delay=10,
                *args,
                **kwargs,
            )
        except RetryError as e:
            self.logger.error(
                f"Database operation failed after retries in {self.__class__.__name__}: {str(e)}"
            )
            raise SQLAlchemyError(f"Database operation failed after retries: {str(e)}")

    def get_by_id(self, entity_id: Any) -> Optional[T]:
        """Get entity by primary key."""

        def _get_by_id():
            return self.db_session.get(self.model_class, entity_id)

        try:
            return self._execute_with_retry(_get_by_id)
        except SQLAlchemyError:
            return None

    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """Get all entities with optional pagination."""

        def _get_all():
            query = select(self.model_class)
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            return list(self.db_session.execute(query).scalars().all())

        try:
            return self._execute_with_retry(_get_all)
        except SQLAlchemyError:
            return []

    def create(self, entity: T) -> T:
        """Create a new entity."""

        def _create():
            self.db_session.add(entity)
            return entity

        return self._execute_with_retry(_create)

    def create_many(self, entities: List[T]) -> List[T]:
        """Create multiple entities."""

        def _create_many():
            self.db_session.add_all(entities)
            return entities

        return self._execute_with_retry(_create_many)

    def update(self, entity: T) -> T:
        """Update an existing entity."""

        def _update():
            self.db_session.merge(entity)
            return entity

        return self._execute_with_retry(_update)

    def delete(self, entity_or_id: T | Any) -> bool:
        """Delete an entity by instance or ID."""

        def _delete():
            if isinstance(entity_or_id, self.model_class):
                entity = entity_or_id
            else:
                entity = self.db_session.get(self.model_class, entity_or_id)
                if not entity:
                    return False

            stmt = delete(self.model_class).where(self.model_class.id == entity.id)
            result = self.db_session.execute(stmt)
            return result.rowcount > 0

        return self._execute_with_retry(_delete)

    def delete_by_id(self, entity_id: Any) -> bool:
        """Delete entity by primary key (legacy method for compatibility)."""
        return self.delete(entity_id)

    def count(self) -> int:
        """Count total entities."""

        def _count():
            stmt = select(func.count(self.model_class.id))
            return self.db_session.execute(stmt).scalar() or 0

        try:
            return self._execute_with_retry(_count)
        except SQLAlchemyError:
            return 0

    def exists(self, entity_id: Any) -> bool:
        """Check if entity exists by ID."""

        def _exists():
            stmt = select(func.count(self.model_class.id)).where(self.model_class.id == entity_id)
            return self.db_session.execute(stmt).first() is not None

        try:
            return self._execute_with_retry(_exists)
        except SQLAlchemyError:
            return False

    @abstractmethod
    def find_by_criteria(self, **criteria) -> List[T]:
        """Find entities by custom criteria. Must be implemented by subclasses."""
        pass
