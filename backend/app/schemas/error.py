from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """
    Standardized inner error payload.
    """
    code: str = Field(..., description="Unique machine-readable error string code")
    message: str = Field(..., description="Human-readable explanation of error condition")


class ErrorResponse(BaseModel):
    """
    Uniform root API error response envelope across all HTTP endpoints.
    """
    error: ErrorDetail
