"""QRicambi API exceptions."""

from __future__ import annotations

from typing import Optional


class QRicambiError(Exception):
    """Base exception for QRicambi API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(QRicambiError):
    """401 Unauthorized — invalid or expired token."""
    pass


class ForbiddenError(QRicambiError):
    """403 Forbidden — insufficient permissions."""
    pass


class NotFoundError(QRicambiError):
    """404 Not Found."""
    pass


class BadRequestError(QRicambiError):
    """400 Bad Request — invalid parameters."""
    pass


class RateLimitError(QRicambiError):
    """Rate limit hit (search requires 30s+ between calls)."""
    pass


class ServerError(QRicambiError):
    """500 Internal Server Error."""
    pass
