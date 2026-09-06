from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AssignmentIntegrityException,
    NoActiveAssignmentException,
    VehicleAccessDeniedException,
)
from app.models.assignment import Assignment
from app.repositories.assignment_repository import AssignmentRepository


class AssignmentService:
    """
    Business service enforcing active assignment resolution and server-side authorization integrity.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.assignment_repo = AssignmentRepository(session)

    async def get_active_assignment_for_user(self, user_id: UUID) -> Assignment:
        """
        Resolves the active assignment for a given user and verifies assignment integrity rules.
        """
        assignment = await self.assignment_repo.get_active_by_user_id(user_id)
        if not assignment:
            raise NoActiveAssignmentException("No active route/vehicle assignment found for this user.")

        # Invariant Verification: vehicle.route_id MUST equal assignment.route_id
        if assignment.vehicle.route_id != assignment.route_id:
            raise AssignmentIntegrityException(
                f"Assignment integrity violation: Assigned vehicle '{assignment.vehicle.vehicle_code}' "
                f"(route_id={assignment.vehicle.route_id}) does not match assigned route '{assignment.route.code}' "
                f"(route_id={assignment.route_id})."
            )

        return assignment

    async def validate_vehicle_access(self, user_id: UUID, target_vehicle_id: UUID) -> Assignment:
        """
        Server-Side Authorization Boundary:
        Verifies that the requested vehicle_id matches the user's active assignment.
        Raises VehicleAccessDeniedException (HTTP 403) on unauthorized access attempt.
        """
        active_assignment = await self.get_active_assignment_for_user(user_id)

        if active_assignment.vehicle_id != target_vehicle_id:
            raise VehicleAccessDeniedException("You are not authorized to access this vehicle.")

        return active_assignment
