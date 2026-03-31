"""
Base repository class with common CRUD operations.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import TypeVar, Generic, List, Optional

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Generic repository for common CRUD operations."""

    def __init__(self, session: AsyncSession, model_class: type):
        self.session = session
        self.model_class = model_class

    async def create(self, obj_in: dict) -> T:
        """Create a new record."""
        db_obj = self.model_class(**obj_in)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def get_by_id(self, id: int) -> Optional[T]:
        """Retrieve a record by ID."""
        return await self.session.get(self.model_class, id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Retrieve all records with pagination."""
        query = select(self.model_class).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(self, id: int, obj_in: dict) -> Optional[T]:
        """Update a record by ID."""
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return None
        for key, value in obj_in.items():
            setattr(db_obj, key, value)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, id: int) -> bool:
        """Delete a record by ID."""
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return False
        await self.session.delete(db_obj)
        await self.session.commit()
        return True
