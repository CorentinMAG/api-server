from sqlalchemy import func, event, Engine, inspect, select, Select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime


@event.listens_for(Engine, "connect")
def enable_fx(dbapi_connection, _):
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        # the sqlite3 driver will not set PRAGMA foreign_keys
        # if autocommit=False; set to True temporarily
        # The autocommit property doesn't exist in python3.10 (need python>=3.12)
        # ac = dbapi_connection.autocommit
        # dbapi_connection.autocommit = True
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

        # restore previous autocommit setting
        # dbapi_connection.autocommit = ac


class Base(DeclarativeBase):

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), index=True)
    updated_at: Mapped[datetime | None] = mapped_column(
        default=None, onupdate=func.now()
    )

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: ({', '.join([f'{c.key}={getattr(self, c.key)}' for c in self.__table__.columns])}"

    def update(self, data: dict[str, any]) -> None:
        """update model attributes from a dictionnary"""
        for key, value in data.items():
            if hasattr(self, key) and key not in (
                "id",
                "created_at",
                "updated_at",
                "uid",
            ):
                # handle nested relationships
                if key in self.__mapper__.relationships.keys():
                    relation = getattr(self, key)
                    if relation is not None and isinstance(value, dict):
                        relation.update(value)
                    continue
                # handle regular columns
                if key in self.__mapper__.column_attrs.keys():
                    setattr(self, key, value)

    @classmethod
    def get_column_from_path(cls, attr_path: str) -> tuple[any, list[str]]:
        """
        Parse a dot-notation attribute path and return the target column + join table names.

        Args:
            attr_path: Dot-separated attribute name (e.g., 'parameter.use_ssl')

        Returns:
            Tuple of (column_object, list_of_join_table_names)

        Raises:
            ValueError: If attribute or relationship doesn't exist
        """
        if not attr_path or "." not in attr_path:
            # Simple column on current model
            try:
                mapper = inspect(cls)
                column = getattr(cls, attr_path)
                return column, []
            except AttributeError as e:
                raise ValueError(
                    f"Attribute '{attr_path}' not found on {cls.__name__}"
                ) from e

        parts = attr_path.split(".")
        joins_needed = []
        current_class = cls

        for i, part in enumerate(parts[:-1]):
            # Get the relationship property
            try:
                rel_property = inspect(current_class).relationships[part]
            except KeyError:
                raise ValueError(
                    f"Relationship '{part}' not found on {current_class.__name__} "
                    f"(path: {'.'.join(parts[:i+1])})"
                )

            # Store the relationship name for joining
            joins_needed.append(part)

            # Move to the next model in the chain
            current_class = rel_property.mapper.class_

        # Get the final column from the last model
        final_attr = parts[-1]
        try:
            final_column = getattr(current_class, final_attr)
        except AttributeError:
            raise ValueError(
                f"Attribute '{final_attr}' not found on {current_class.__name__} "
                f"(path: {attr_path})"
            )

        return final_column, joins_needed

    @classmethod
    def apply_filter(cls, filters: dict[str, any]) -> Select:
        """
        Apply multiple filters to a query using dot-notation attribute paths.

        Args:
            filters: Dict mapping attribute paths to values
                     Example: {'id': 1, 'parameter.use_ssl': True}
        Returns:
            Query object with all filters applied
        """
        stmt = select(cls)

        for attr_path, value in filters.items():
            if value is None:
                continue

            column, joins_needed = cls.get_column_from_path(attr_path)

            # Add necessary joins for relationships
            for join_name in joins_needed:
                stmt = stmt.join(getattr(cls, join_name))

            # Apply the filter condition
            if isinstance(value, (list, tuple)):
                stmt = stmt.where(column.in_(value))
            else:
                stmt = stmt.where(column == value)
        return stmt
