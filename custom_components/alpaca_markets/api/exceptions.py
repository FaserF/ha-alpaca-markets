"""Exceptions for the Alpaca Markets API client."""

from __future__ import annotations


class AlpacaError(Exception):
    """Base exception for Alpaca API errors."""


class AlpacaAuthError(AlpacaError):
    """Raised when authentication fails (401/403)."""


class AlpacaConnectionError(AlpacaError):
    """Raised when the API cannot be reached."""


class AlpacaTimeoutError(AlpacaConnectionError):
    """Raised when a request times out."""


class AlpacaAPIError(AlpacaError):
    """Raised when the API returns an unexpected error."""

    def __init__(self, status: int, message: str) -> None:
        """Initialize with HTTP status code and message."""
        self.status = status
        super().__init__(f"HTTP {status}: {message}")


class AlpacaRateLimitError(AlpacaAPIError):
    """Raised when the API rate limit is exceeded (429)."""
