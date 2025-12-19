"""Authentication module for Azure PIM CLI."""

import base64
import json
import os
import socket
from contextlib import contextmanager
from typing import Optional

from azure.identity import AzureCliCredential, DefaultAzureCredential

# Store original getaddrinfo for selective IPv4 forcing
_original_getaddrinfo = socket.getaddrinfo


@contextmanager
def ipv4_only_context():
    """
    Context manager that temporarily forces IPv4-only DNS resolution.
    This works around DNS resolution issues with IPv6 on some networks.

    Usage:
        with ipv4_only_context():
            # Network calls here will use IPv4 only
            response = requests.get(url)
    """

    def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        """Force IPv4 resolution to avoid IPv6 DNS issues"""
        return _original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

    original = socket.getaddrinfo
    socket.getaddrinfo = _ipv4_only_getaddrinfo
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
    return os.environ.get("AZ_PIM_IPV4_ONLY", "").lower() in ("1", "true", "yes")


class AzureAuth:
    """Handle Azure authentication using Azure SDK."""

    def __init__(self) -> None:
        """Initialize Azure authentication."""
        self._credential: Optional[AzureCliCredential] = None
        self._default_credential: Optional[DefaultAzureCredential] = None
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
            except Exception:
                raise AuthenticationError(
                    "No Azure credentials available",
                    suggestion=(
                        "Run 'az login' to authenticate with Azure CLI, "
                        "or configure Azure SDK credentials "
                        "(service principal, managed identity, etc.)"
                    ),
                )

        try:
            # Test the credential
            self._default_credential.get_token("https://management.azure.com/.default")
            return self._default_credential
        except Exception as e:
            raise AuthenticationError(
                f"Failed to acquire access token: {str(e)}",
                suggestion=(
                    "Run 'az login' to authenticate with Azure CLI, "
                    "or check your network connection"
                ),
            )

    def get_token(self, scope: str = "https://management.azure.com/.default") -> str:
        """
        Get an access token for the specified scope.

        Args:
            scope: The scope for the access token

        Returns:
            Access token string

        Raises:
            AuthenticationError: If token cannot be acquired
        """
        try:
            credential = self._get_credential()
            token = credential.get_token(scope)
            return token.token
        except Exception as e:
            from az_pim_cli.exceptions import AuthenticationError

            raise AuthenticationError(
                f"Failed to acquire access token: {str(e)}",
                suggestion=(
                    "Run 'az login' to authenticate with Azure CLI, "
                    "or check your network connection"
                ),
            )

    def _extract_token_claim(self, scope: str, claim: str) -> Optional[str]:
        """
        Extract a claim from the JWT token payload.

        Args:
            scope: The scope for the access token
            claim: The claim name to extract (e.g., 'oid', 'tid')

        Returns:
            The claim value or None if not found
        """
        try:
            token = self.get_token(scope)
            payload_part = token.split(".")[1]

            # Add padding if needed (JWT base64 may not be padded)
            padding = len(payload_part) % 4
            if padding:
                payload_part += "=" * (4 - padding)

            decoded = base64.urlsafe_b64decode(payload_part)
            claims = json.loads(decoded)

            return claims.get(claim)
        except Exception:
            return None

    def get_tenant_id(self) -> str:
        """
        Get the current tenant ID from the access token.

        Returns:
            Tenant ID string

        Raises:
            RuntimeError: If tenant ID cannot be determined
        """
        tenant_id = self._extract_token_claim("https://management.azure.com/.default", "tid")

        if tenant_id:
            return tenant_id

        raise RuntimeError(
            "Failed to get tenant ID from token claims. "
            "Ensure you have successfully logged in with 'az login'."
        )

    def get_subscription_id(self) -> str:
        """
        Get the current subscription ID.

        Returns:
            Subscription ID string

        Raises:
            RuntimeError: If subscription ID cannot be determined
        """
        # Try to get from token claims (some tokens include this)
        subscription_id = self._extract_token_claim(
            "https://management.azure.com/.default", "subscriptionId"
        )

        if subscription_id:
            return subscription_id

        # If not in token, we need to query the Azure SDK
        # Use the subscription context from the credential
        try:
            from azure.mgmt.subscription import SubscriptionClient

            credential = self._get_credential()
            client = SubscriptionClient(credential)

            for subscription in client.subscriptions.list():
                if subscription.subscription_id:
                    return subscription.subscription_id

            raise RuntimeError("No subscriptions found for the authenticated user")
        except Exception as e:
            raise RuntimeError(
                f"Failed to determine subscription ID: {str(e)}. "
                "Ensure you have selected a subscription with 'az account set --subscription <sub>'."
            )

    def get_user_object_id(self, scope: str = "https://management.azure.com/.default") -> str:
        """
        Get the current user's object ID from the access token claims.

        Args:
            scope: The scope for the access token (ARM or Graph)

        Returns:
            User object ID string

        Raises:
            RuntimeError: If object ID cannot be determined
        """
        object_id = self._extract_token_claim(scope, "oid")

        if object_id:
            return object_id

        raise RuntimeError(
            "Failed to get user object ID from token claims. "
            "Ensure you have successfully logged in with 'az login'."
        )
