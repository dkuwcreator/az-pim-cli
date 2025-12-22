"""Azure CLI credential authentication for az-pim-cli."""

import base64
import json
import os
import socket
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from azure.identity import AzureCliCredential, DefaultAzureCredential

# Store original getaddrinfo for selective IPv4 forcing
_original_getaddrinfo = socket.getaddrinfo


@contextmanager
def ipv4_only_context() -> Generator[None, None, None]:
    """
    Context manager that temporarily forces IPv4-only DNS resolution.
    This works around DNS resolution issues with IPv6 on some networks.

    Usage:
        with ipv4_only_context():
            # Network calls here will use IPv4 only
            response = requests.get(url)
    """

    def _ipv4_only_getaddrinfo(
        host: str, port: int | str, family: int = 0, type: int = 0, proto: int = 0, flags: int = 0
    ) -> Any:
        """Force IPv4 resolution to avoid IPv6 DNS issues"""
        return _original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

    original = socket.getaddrinfo
    socket.getaddrinfo = _ipv4_only_getaddrinfo  # type: ignore[assignment]
    try:
        yield
    finally:
        socket.getaddrinfo = original


def should_use_ipv4_only() -> bool:
    """
    Check if IPv4-only mode should be enabled.
    Can be controlled via AZ_PIM_IPV4_ONLY environment variable.

    Returns:
        True if IPv4-only mode is enabled
    """
    return os.environ.get("AZ_PIM_IPV4_ONLY", "").strip().lower() in ("1", "true", "yes")


class AzureAuth:
    """Handle Azure authentication using Azure SDK."""

    def __init__(self) -> None:
        """Initialize Azure authentication."""
        self._credential: AzureCliCredential | None = None
        self._default_credential: DefaultAzureCredential | None = None
        self._token_cache: dict[str, dict] = {}

    def _get_credential(self) -> AzureCliCredential | DefaultAzureCredential:
        """
        Get the appropriate credential for authentication.
        Tries AzureCliCredential first (uses cached Azure CLI login),
        then falls back to DefaultAzureCredential.

        Returns:
            Azure credential instance

        Raises:
            AuthenticationError: If no credentials are available
        """
        from az_pim_cli.exceptions import AuthenticationError

        if self._credential is None:
            try:
                self._credential = AzureCliCredential()
            except Exception:
                pass

        if self._credential is not None:
            try:
                # Test the credential
                self._credential.get_token("https://management.azure.com/.default")
                return self._credential
            except Exception:
                self._credential = None

        if self._default_credential is None:
            try:
                self._default_credential = DefaultAzureCredential()
            except Exception as e:
                raise AuthenticationError(
                    "No Azure credentials available",
                    suggestion=(
                        "Run 'az login' to authenticate with Azure CLI, "
                        "or configure Azure SDK credentials "
                        "(service principal, managed identity, etc.)"
                    ),
                ) from e

        return self._default_credential

    def get_token(self, scope: str = "https://graph.microsoft.com/.default") -> str:
        """
        Get an access token for the specified scope.

        Args:
            scope: The scope for the access token

        Returns:
            Access token string

        Raises:
            AuthenticationError: If unable to get a token
        """
        from az_pim_cli.exceptions import AuthenticationError

        try:
            credential = self._get_credential()

            if should_use_ipv4_only():
                with ipv4_only_context():
                    token = credential.get_token(scope)
            else:
                token = credential.get_token(scope)

            return token.token
        except Exception as e:
            raise AuthenticationError(
                "Failed to get access token",
                suggestion=(
                    "Run 'az login' to authenticate, or verify your credentials are configured"
                ),
            ) from e

    def get_user_object_id(self) -> str:
        """
        Get the object ID of the currently authenticated user.

        Returns:
            User object ID (principal ID)

        Raises:
            AuthenticationError: If unable to get user info
        """
        from az_pim_cli.exceptions import AuthenticationError

        try:
            token = self.get_token("https://graph.microsoft.com/.default")
            payload = token.split(".")[1]
            payload += "=" * (4 - len(payload) % 4)
            claims = json.loads(base64.b64decode(payload))
            return str(claims.get("oid", ""))
        except Exception as e:
            raise AuthenticationError("Failed to get user object ID from token") from e

    def get_tenant_id(self) -> str:
        """
        Get the tenant ID from the token.

        Returns:
            Tenant ID

        Raises:
            AuthenticationError: If unable to get tenant ID
        """
        from az_pim_cli.exceptions import AuthenticationError

        try:
            token = self.get_token("https://graph.microsoft.com/.default")
            payload = token.split(".")[1]
            payload += "=" * (4 - len(payload) % 4)
            claims = json.loads(base64.b64decode(payload))
            return str(claims.get("tid", ""))
        except Exception as e:
            raise AuthenticationError("Failed to get tenant ID from token") from e
