from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import InvalidCredentialsException, UnauthorizedException
from app.core.security import create_access_token, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse


class AuthService:
    """
    Business service handling user authentication and JWT token creation.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def authenticate_user(self, login_data: LoginRequest) -> TokenResponse:
        """
        Authenticates user email and password credentials.
        Returns a signed JWT access token upon successful authentication.
        """
        user = await self.user_repo.get_by_email(login_data.email)
        if not user:
            raise InvalidCredentialsException("Invalid email or password.")

        if not verify_password(login_data.password, user.password_hash):
            raise InvalidCredentialsException("Invalid email or password.")

        if not user.is_active:
            raise UnauthorizedException("User account is disabled.")

        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=str(user.id),
            expires_delta=expires_delta,
            extra_claims={"email": user.email, "role": user.role},
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
