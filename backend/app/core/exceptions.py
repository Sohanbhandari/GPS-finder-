from typing import Any, Optional
from fastapi import status


class AppException(Exception):
    """
    Base application exception for all domain business errors.
    Standardized API response format:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human readable error message"
        }
    }
    """
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Any] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class InvalidCredentialsException(AppException):
    def __init__(self, message: str = "Invalid email or password."):
        super().__init__(
            code="INVALID_CREDENTIALS",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Could not validate authentication credentials."):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class VehicleAccessDeniedException(AppException):
    def __init__(self, message: str = "You are not authorized to access this vehicle."):
        super().__init__(
            code="VEHICLE_ACCESS_DENIED",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class NoActiveAssignmentException(AppException):
    def __init__(self, message: str = "No active route/vehicle assignment found for this user."):
        super().__init__(
            code="NO_ACTIVE_ASSIGNMENT",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class AssignmentIntegrityException(AppException):
    def __init__(self, message: str = "Assigned vehicle does not belong to the target route."):
        super().__init__(
            code="ASSIGNMENT_INTEGRITY_VIOLATION",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class ResourceNotFoundException(AppException):
    def __init__(self, message: str = "Requested resource not found."):
        super().__init__(
            code="NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )
