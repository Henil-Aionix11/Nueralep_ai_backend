"""Base repository for all models.

This repository provides basic CRUD operations and pagination for any model.
It contains following methods:
- create
- create_all
- get_by_id
- get_all
- get_all_by_field
- get_first_by_filter
- get_all_by_filter
- get_paginated
- update
- delete
- delete_by_ids
- commit
- count_by_filter
- get_by_field
"""

from typing import Any, Generic, Optional, TypeVar, cast, Union
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import (
    Table,
    func,
    or_,
    select,
    delete as sql_delete,
    update as sql_update,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel
from sqlalchemy import desc as sql_desc, asc as sql_asc

from app.core.exceptions.api_exceptions import (
    ApiConflictError,
    ApiInternalServerError,
    ApiNotFoundError,
)
from app.core.schema.pagination_schema import PaginationParams


Model = TypeVar("Model", bound=SQLModel)
CreateSchema = TypeVar("CreateSchema", bound=BaseModel)
UpdateSchema = TypeVar("UpdateSchema", bound=BaseModel)


class BaseRepository(Generic[Model, CreateSchema, UpdateSchema]):
    """Base repository class providing CRUD operations for database models."""

    def __init__(self, model: type[Model], session: AsyncSession) -> None:
        """Initialize repository with model and session.

        Args:
            model: SQLModel class
            session: Async database session
        """
        self.model = model
        self.session = session
        # Cast model to access SQLAlchemy table attributes
        model_table = cast(Table, getattr(self.model, "__table__", None))
        self.unique_fields = set()

        if model_table is not None:
            self.unique_fields = {
                column.name
                for column in model_table.columns
                if column.unique or column.primary_key
            }

    async def get_by_id(self, record_id: Union[UUID, int]) -> Model | None:
        """Retrieve a record by its ID.

        Args:
            record_id: Record ID (UUID or int)

        Returns:
            Model instance or None if not found
        """
        return await self.session.get(self.model, record_id)

    async def create(
        self, obj_in: CreateSchema | dict, commit: bool = True, refresh: bool = True
    ) -> Model:
        """Create single record with validation.

        Args:
            obj_in: Input schema or dict
            commit: Whether to commit immediately
            refresh: Whether to refresh after commit

        Returns:
            Created model instance

        Raises:
            ApiConflictError: If duplicate entry or integrity violation
        """
        try:
            # Handle dict input
            if isinstance(obj_in, dict):
                input_data = obj_in
            else:
                # Get the data from the input schema
                input_data = obj_in.model_dump()

            # Create the model instance
            db_obj = self.model(**input_data)
            self.session.add(db_obj)

            if commit:
                await self.session.commit()
                if refresh:
                    await self.session.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            await self.session.rollback()
            raise ApiConflictError(
                error=f"Duplicate entry: {e.orig!s}",
                message=f"Duplicate entry: {e.orig!s}",
            ) from e

    async def create_all(
        self, objs_in: list[CreateSchema | dict], commit: bool = True
    ) -> list[Model]:
        """Bulk create with transaction safety.

        Args:
            objs_in: List of input schemas or dicts
            commit: Whether to commit immediately

        Returns:
            List of created model instances

        Raises:
            ApiConflictError: If duplicate entry or integrity violation
        """
        try:
            db_objs = []
            for obj in objs_in:
                if isinstance(obj, dict):
                    db_objs.append(self.model(**obj))
                else:
                    db_objs.append(self.model(**obj.model_dump()))

            self.session.add_all(db_objs)

            if commit:
                await self.session.commit()
                # Refresh all objects after commit
                for db_obj in db_objs:
                    await self.session.refresh(db_obj)
            return db_objs
        except IntegrityError as e:
            await self.session.rollback()
            raise ApiConflictError(
                error=f"Duplicate entry in bulk operation: {e.orig!s}",
                message=f"Duplicate entry in bulk operation: {e.orig!s}",
            ) from e

    async def get_all(
        self, include_metadata: bool = False
    ) -> list[Model] | tuple[list[Model], int]:
        """Get all records without pagination.

        Args:
            include_metadata: Whether to return count with results

        Returns:
            List of records or tuple of (records, count)
        """
        query = select(self.model)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        if include_metadata:
            total = len(items)
            return items, total
        return items

    async def get_paginated(
        self,
        params: PaginationParams,
    ) -> tuple[list[Model], int]:
        """Advanced query with pagination/search/sort.

        Args:
            params: Pagination parameters including filters, search, and sort

        Returns:
            Tuple of (records, total_count)
        """
        # Start with the base query
        query = select(self.model)

        # Apply filters
        if params.filters:
            query = query.filter_by(**params.filters)

        # Apply search
        if params.search and params.search_fields:
            conditions = [
                getattr(self.model, f).ilike(f"%{params.search}%")
                for f in params.search_fields
            ]
            query = query.filter(or_(*conditions))

        # Apply sorting
        if params.sort_by and hasattr(self.model, params.sort_by):
            order = getattr(self.model, params.sort_by)
            query = query.order_by(
                order.desc() if params.sort_order.lower() == "desc" else order
            )

        # Execute count and pagination
        count_query = select(func.count()).select_from(query.subquery())
        total: int = await self.session.scalar(count_query) or 0
        offset = (params.page - 1) * params.page_size
        result = await self.session.execute(
            query.offset(offset).limit(params.page_size)
        )

        return list(result.scalars().all()), total

    async def update(
        self,
        record_id: Union[UUID, int],
        update_data: UpdateSchema | dict[str, Any],
        commit: bool = True,
    ) -> Model:
        """Update a record by its ID.

        Args:
            record_id: Record ID (UUID or int)
            update_data: Update schema or dict
            commit: Whether to commit immediately

        Returns:
            Updated model instance

        Raises:
            ApiNotFoundError: If record not found
            ApiConflictError: If integrity violation
            ApiInternalServerError: If update fails
        """
        existing_obj = await self.get_by_id(record_id)
        if not existing_obj:
            raise ApiNotFoundError(
                error=f"{self.model.__name__} with id {record_id} not found",
                message=f"{self.model.__name__} with id {record_id} not found",
            )

        update_dict = (
            update_data
            if isinstance(update_data, dict)
            else update_data.model_dump(exclude_unset=True)
        )

        try:
            for field, value in update_dict.items():
                setattr(existing_obj, field, value)

            if commit:
                await self.session.commit()
                await self.session.refresh(existing_obj)

            return existing_obj

        except IntegrityError as e:
            await self.session.rollback()
            raise ApiConflictError(
                error=f"Conflict during update: {e.orig!s}",
                message=f"Conflict during update: {e.orig!s}",
            ) from e
        except Exception as e:
            await self.session.rollback()
            raise ApiInternalServerError(
                error=f"Update failed: {e!s}", message=f"Update failed: {e!s}"
            ) from e

    async def delete(self, db_obj: Model) -> bool:
        """Hard delete with error handling.

        Args:
            db_obj: Model instance to delete

        Returns:
            True if successful

        Raises:
            ApiConflictError: If foreign key constraint violation
            ApiInternalServerError: If deletion fails
        """
        try:
            await self.session.delete(db_obj)
            await self.session.commit()
            return True
        except IntegrityError as e:
            await self.session.rollback()
            raise ApiConflictError(
                error=f"Cannot delete: {e.orig!s}", message=f"Cannot delete: {e.orig!s}"
            ) from e
        except Exception as e:
            await self.session.rollback()
            raise ApiInternalServerError(
                error=f"Deletion failed: {e!s}", message=f"Deletion failed: {e!s}"
            ) from e

    async def delete_by_ids(self, record_ids: list[Union[UUID, int]]) -> int:
        """Bulk delete records by IDs.

        Args:
            record_ids: List of record IDs

        Returns:
            Number of deleted records

        Raises:
            ApiInternalServerError: If bulk deletion fails
        """
        try:
            query = sql_delete(self.model).where(self.model.id.in_(record_ids))
            result = await self.session.execute(query)
            await self.session.commit()
            return result.rowcount
        except Exception as e:
            await self.session.rollback()
            raise ApiInternalServerError(
                error=f"Bulk deletion failed: {e!s}",
                message=f"Bulk deletion failed: {e!s}",
            ) from e

    async def get_by_field(self, field: str, value: Any) -> Model | None:
        """Get a single record by unique field.

        Args:
            field: The field name to query by
            value: The value to search for

        Returns:
            The record if found, None otherwise

        Raises:
            ValueError: If the field is not unique
        """
        if field not in self.unique_fields:
            raise ValueError(
                f"Field '{field}' is not unique in {self.model.__name__}. "
                "Only unique fields can be used for single-record lookup."
            )

        query = select(self.model).where(getattr(self.model, field) == value)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_by_field(self, field: str, value: Any) -> list[Model]:
        """Get all records matching a field value (non-unique fields allowed).

        Args:
            field: Field name to filter by
            value: Value to match

        Returns:
            List of matching records
        """
        query = select(self.model).where(getattr(self.model, field) == value)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_by_filter(
        self,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        limit: Optional[int] = None,
        **filters,
    ) -> list[Model]:
        """Get all records matching filters with optional ordering.

        Args:
            order_by: Field name to order by
            order_desc: If True, order descending (default: ascending)
            limit: Maximum number of records to return
            **filters: Field-value pairs to filter by

        Returns:
            List of matching records
        """
        query = select(self.model).filter_by(**filters)

        # Apply ordering if specified
        if order_by and hasattr(self.model, order_by):
            order_field = getattr(self.model, order_by)
            query = query.order_by(
                sql_desc(order_field) if order_desc else sql_asc(order_field)
            )

        # Apply limit if specified
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_first_by_filter(self, **filters) -> Model | None:
        """Get first record matching filters.

        Args:
            **filters: Field-value pairs to filter by

        Returns:
            First matching record or None
        """
        query = select(self.model).filter_by(**filters).limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def count_by_filter(self, **filters) -> int:
        """Count records matching filters.

        Args:
            **filters: Field-value pairs to filter by

        Returns:
            Count of matching records
        """
        query = select(func.count()).select_from(self.model).filter_by(**filters)
        result = await self.session.scalar(query)
        return result or 0

    async def commit(self) -> None:
        """Explicit commit for multi-operation transactions."""
        await self.session.commit()

    async def increment_field(
        self,
        field_name: str,
        increment_by: int = 1,
        filters: Optional[dict] = None,
        record_id: Optional[Union[UUID, int]] = None,
    ) -> int:
        """Atomically increment a numeric field with optional filters.

        This method performs an atomic SQL increment operation, which is:
        - Thread-safe (no race conditions)
        - Efficient (single SQL query)
        - Conditional (can filter which records to update)

        Args:
            field_name: Name of the field to increment (e.g., "query_count")
            increment_by: Amount to increment by (default: 1, use negative for decrement)
            filters: Optional dict of field-value pairs for WHERE clause
            record_id: Optional specific record ID to update

        Returns:
            Number of rows affected

        Example:
            # Increment query_count for non-subscribed users only
            await repo.increment_field(
                field_name="query_count",
                filters={"is_subscribed": False},
                record_id=user_id
            )
        """
        if not hasattr(self.model, field_name):
            raise ValueError(
                f"Field '{field_name}' does not exist in {self.model.__name__}"
            )

        # Build query
        field = getattr(self.model, field_name)
        query = sql_update(self.model).values(**{field_name: field + increment_by})

        # Apply record ID filter if provided
        if record_id is not None:
            query = query.where(self.model.id == record_id)

        # Apply additional filters if provided
        if filters:
            for key, value in filters.items():
                if not hasattr(self.model, key):
                    raise ValueError(
                        f"Filter field '{key}' does not exist in {self.model.__name__}"
                    )
                query = query.where(getattr(self.model, key) == value)

        # Execute and return affected rows
        try:
            result = await self.session.execute(query)
            await self.session.commit()
            return result.rowcount
        except Exception as e:
            await self.session.rollback()
            raise ApiInternalServerError(
                error=f"Failed to increment field {field_name}: {e!s}",
                message=f"Failed to increment field {field_name}: {e!s}",
            ) from e
