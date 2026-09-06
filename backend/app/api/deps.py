from uuid import UUID
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.assignment import Assignment
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.assignment_service import AssignmentService

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI security dependency resolving authenticated user from HTTP Bearer JWT token.
    Raises UnauthorizedException (HTTP 401) on missing, malformed, or expired token.
    """
    if not credentials or not credentials.credentials:
        raise UnauthorizedException("Missing Authorization Header.")

    payload = decode_access_token(credentials.credentials)
    sub = payload.get("sub")
    if not sub:
        raise UnauthorizedException("Token sub claim missing.")

    try:
        user_id = UUID(sub)
    except ValueError as err:
        raise UnauthorizedException("Invalid user ID format in token.") from err

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise UnauthorizedException("User associated with token no longer exists.")

    if not user.is_active:
        raise UnauthorizedException("User account is disabled.")

    return user


async def get_active_assignment(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Assignment:
    """
    FastAPI dependency resolving active assignment for the current authenticated user.
    Enforces active assignment presence (HTTP 404) and assignment integrity (HTTP 400).
    """
    assignment_service = AssignmentService(db)
    return await assignment_service.get_active_assignment_for_user(current_user.id)


async def verify_vehicle_access(
    vehicle_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Assignment:
    """
    FastAPI authorization dependency enforcing server-side vehicle access control.
    Raises VehicleAccessDeniedException (HTTP 403) if target vehicle_id does not match active assignment.
    """
    assignment_service = AssignmentService(db)
    return await assignment_service.validate_vehicle_access(current_user.id, vehicle_id)
