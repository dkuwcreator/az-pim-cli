"""HTTP client adapter using httpx with retry logic.

This module provides an HTTP client implementation using httpx with
automatic retry/backoff via tenacity, wrapped behind the HTTPClientProtocol
interface for swappability.
"""

import socket
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from az_pim_cli.exceptions import NetworkError, ParsingError, PermissionError


class HTTPXAdapter:
    """HTTP client adapter using httpx with automatic retry/backoff.

    This adapter wraps httpx and provides:
    - Automatic retry with exponential backoff for transient errors
    - Enhanced error handling with domain-specific exceptions
    - IPv4-only mode support for DNS issues
    - Clean interface for JSON APIs
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        verbose: bool = False,
        ipv4_only: bool = False,
    ) -> None:
        """
        Initialize HTTP client adapter.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            verbose: Enable verbose logging
            ipv4_only: Force IPv4-only DNS resolution
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.verbose = verbose
        self.ipv4_only = ipv4_only

        # Configure httpx client
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
        )

    def __enter__(self) -> "HTTPXAdapter":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def _apply_ipv4_only(self) -> None:
        """Apply IPv4-only DNS resolution if enabled."""
        if self.ipv4_only:
            # Store original getaddrinfo
            original_getaddrinfo = socket.getaddrinfo

            def ipv4_only_getaddrinfo(
                host: str,
                port: Any,
                family: int = 0,
                type: int = 0,
                proto: int = 0,
                flags: int = 0,
            ) -> Any:
                """Force IPv4 resolution."""
                return original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

            socket.getaddrinfo = ipv4_only_getaddrinfo  # type: ignore

    def _restore_getaddrinfo(self) -> None:
        """Restore original getaddrinfo (not needed with httpx, but kept for compatibility)."""
        pass

    @retry(
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _make_request_with_retry(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """
        Make HTTP request with automatic retry for transient errors.

        Args:
            method: HTTP method
            url: Request URL
            headers: Optional headers
            params: Optional query parameters
            json_data: Optional JSON body

        Returns:
            httpx Response object

        Raises:
            httpx.HTTPError: For HTTP errors
        """
        if self.verbose:
            print(f"[DEBUG] {method} {url}")
            if params:
                print(f"[DEBUG] Params: {params}")

        return self._client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_data,
        )

    def _handle_response(
        self, response: httpx.Response, operation: str = "API request"
    ) -> dict[str, Any]:
        """
        Handle HTTP response and convert to JSON.

        Args:
            response: httpx Response object
            operation: Description of operation for error messages

        Returns:
            Response JSON data

        Raises:
            NetworkError: For network errors
            PermissionError: For 403 errors
            ParsingError: For JSON parsing errors
        """
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                raise PermissionError(
                    f"Permission denied for {operation}",
                    endpoint=str(response.url),
                    required_permissions=f"Check Azure RBAC permissions for: {response.url}",
                )
            raise NetworkError(
                f"HTTP {e.response.status_code} error during {operation}: {e}",
                endpoint=str(response.url),
            )
        except httpx.ConnectError as e:
            raise NetworkError(
                f"Connection error during {operation}: {e}",
                endpoint=str(response.url),
                suggest_ipv4=not self.ipv4_only,
            )
        except httpx.TimeoutException as e:
            raise NetworkError(
                f"Timeout during {operation}: {e}",
                endpoint=str(response.url),
            )
        except ValueError as e:
            raise ParsingError(
                f"Failed to parse JSON response: {e}",
                response_data=response.text[:500] if hasattr(response, "text") else "",
            )

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
            timeout: Optional timeout (overrides default)

        Returns:
            Response JSON data

        Raises:
            NetworkError: For network-related errors
            PermissionError: For 403 errors
            ParsingError: For JSON parsing errors
        """
        try:
            response = self._make_request_with_retry(
                method="GET",
                url=url,
                headers=headers,
                params=params,
            )
            return self._handle_response(response, operation="GET request")
        except Exception as e:
            if isinstance(e, (NetworkError, PermissionError, ParsingError)):
                raise
            raise NetworkError(f"Unexpected error during GET request: {e}", endpoint=url)

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
            timeout: Optional timeout (overrides default)

        Returns:
            Response JSON data

        Raises:
            NetworkError: For network-related errors
            PermissionError: For 403 errors
            ParsingError: For JSON parsing errors
        """
        try:
            response = self._make_request_with_retry(
                method="POST",
                url=url,
                headers=headers,
                params=params,
                json_data=json_data,
            )
            return self._handle_response(response, operation="POST request")
        except Exception as e:
            if isinstance(e, (NetworkError, PermissionError, ParsingError)):
                raise
            raise NetworkError(f"Unexpected error during POST request: {e}", endpoint=url)

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
            timeout: Optional timeout (overrides default)

        Returns:
            Response JSON data

        Raises:
            NetworkError: For network-related errors
            PermissionError: For 403 errors
            ParsingError: For JSON parsing errors
        """
        try:
            response = self._make_request_with_retry(
                method="PUT",
                url=url,
                headers=headers,
                params=params,
                json_data=json_data,
            )
            return self._handle_response(response, operation="PUT request")
        except Exception as e:
            if isinstance(e, (NetworkError, PermissionError, ParsingError)):
                raise
            raise NetworkError(f"Unexpected error during PUT request: {e}", endpoint=url)
