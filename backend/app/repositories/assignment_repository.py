from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment


class AssignmentRepository:
    """
    Data access repository for Assignment entity queries.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_by_user_id(self, user_id: UUID) -> Optional[Assignment]:
        """
        Retrieves the active assignment for a user where is_active = True.
        """
        stmt = (
            select(Assignment)
            .where(Assignment.user_id == user_id, Assignment.is_active == True)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, assignment_id: UUID) -> Optional[Assignment]:
        """
        Retrieves an assignment by primary key UUID.
        """
        stmt = select(Assignment).where(Assignment.id == assignment_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
