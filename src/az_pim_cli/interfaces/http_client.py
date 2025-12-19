"""HTTP client protocol interface.

This module defines the protocol (interface) for HTTP clients,
allowing the infrastructure implementation to be swappable.
"""

from typing import Any, Protocol


class HTTPClientProtocol(Protocol):
    """Protocol for HTTP client operations."""

    def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """
        Make a GET request.

        Args:
            url: The URL to request
            headers: Optional headers
            params: Optional query parameters
            timeout: Optional timeout in seconds

        Returns:
            Response JSON data

        Raises:
            NetworkError: For network-related errors
            PermissionError: For 403 errors
            ParsingError: For JSON parsing errors
        """
        ...

    def post(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """
        Make a POST request.

        Args:
            url: The URL to request
            headers: Optional headers
            params: Optional query parameters
            json_data: Optional JSON body
            timeout: Optional timeout in seconds

        Returns:
            Response JSON data

        Raises:
            NetworkError: For network-related errors
            PermissionError: For 403 errors
            ParsingError: For JSON parsing errors
        """
        ...

    def put(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """
        Make a PUT request.

        Args:
            url: The URL to request
            headers: Optional headers
            params: Optional query parameters
            json_data: Optional JSON body
            timeout: Optional timeout in seconds

        Returns:
            Response JSON data

        Raises:
            NetworkError: For network-related errors
            PermissionError: For 403 errors
            ParsingError: For JSON parsing errors
        """
        ...
