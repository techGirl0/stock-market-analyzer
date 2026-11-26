"""Shared create/conflict handling for the FastCRUD-backed services."""

from typing import Any

from fastcrud import FastCRUD
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BackendError


async def create_record(
    crud: FastCRUD[Any, Any, Any, Any, Any, Any],
    session: AsyncSession,
    payload: BaseModel,
    read_schema: type[BaseModel],
) -> Any:
    """Insert one record and commit; internal_error when nothing is returned."""
    record = await crud.create(db=session, object=payload, schema_to_select=read_schema)
    await session.commit()
    if record is None:
        raise BackendError("internal_error", "The record could not be created.", 500)
    return record


async def create_unique(
    crud: FastCRUD[Any, Any, Any, Any, Any, Any],
    session: AsyncSession,
    payload: BaseModel,
    read_schema: type[BaseModel],
    conflict_message: str,
) -> Any:
    """Insert one record; unique-constraint violations become a 409 conflict."""
    try:
        return await create_record(crud, session, payload, read_schema)
    except IntegrityError as exc:
        await session.rollback()
        raise BackendError("resource_conflict", conflict_message, 409) from exc
