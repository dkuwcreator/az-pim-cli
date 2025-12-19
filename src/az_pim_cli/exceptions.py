"""Custom exceptions for Azure PIM CLI.

DEPRECATION NOTICE:
    This module provides backward compatibility. New code should import from
    az_pim_cli.domain.exceptions instead.
"""

# Import from domain layer for backward compatibility
from az_pim_cli.domain.exceptions import (  # noqa: F401
    AuthenticationError,
    NetworkError,
    ParsingError,
    PermissionError,
    PIMError,
)

__all__ = [
    "PIMError",
    "NetworkError",
    "PermissionError",
    "AuthenticationError",
    "ParsingError",
]
