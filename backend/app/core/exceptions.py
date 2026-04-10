"""Custom application exceptions."""

from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    """404 Not Found — requested resource does not exist."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ForbiddenError(HTTPException):
    """403 Forbidden — authenticated but lacking permission."""

    def __init__(self, detail: str = "Access forbidden") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ConflictError(HTTPException):
    """409 Conflict — duplicate or state-violating operation."""

    def __init__(self, detail: str = "Resource conflict") -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class BadRequestError(HTTPException):
    """400 Bad Request — invalid or malformed input."""

    def __init__(self, detail: str = "Bad request") -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UnauthorizedError(HTTPException):
    """401 Unauthorized — missing or invalid authentication."""

    def __init__(self, detail: str = "Invalid credentials") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class MembershipRequiredError(HTTPException):
    """402 Payment Required — host must have an active membership."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active membership required to perform this action",
        )
