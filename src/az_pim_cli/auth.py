"""Authentication module for Azure PIM CLI."""

import base64
import json
import socket
import subprocess
from typing import Optional

from azure.identity import DefaultAzureCredential, AzureCliCredential

# Monkey-patch socket.getaddrinfo to force IPv4 resolution only
# This works around DNS resolution issues with IPv6 on some networks
_original_getaddrinfo = socket.getaddrinfo

def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    """Force IPv4 resolution to avoid IPv6 DNS issues"""
    return _original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

socket.getaddrinfo = _ipv4_only_getaddrinfo


class AzureAuth:
    """Handle Azure authentication using Azure CLI or MSAL."""

    def __init__(self) -> None:
        """Initialize Azure authentication."""
        self._credential: Optional[DefaultAzureCredential] = None
        self._cli_credential: Optional[AzureCliCredential] = None

    def get_token(self, scope: str = "https://management.azure.com/.default") -> str:
        """
        Get an access token for the specified scope using Azure CLI directly.
        This works offline by using cached credentials from Azure CLI.

        Args:
            scope: The scope for the access token

        Returns:
            Access token string
        """
        try:
            # Convert scope to resource URL (remove /.default suffix)
            resource = scope.replace("/.default", "")
            
            # Get token directly from Azure CLI - uses local cache, works offline
            result = subprocess.run(
                ["az", "account", "get-access-token", "--resource", resource, "-o", "json"],
                capture_output=True,
                text=True,
                check=True,
            )
            token_data = json.loads(result.stdout)
            return token_data["accessToken"]
        except Exception as e:
            # Fallback to azure.identity library methods
            try:
                if self._cli_credential is None:
                    self._cli_credential = AzureCliCredential()
                token = self._cli_credential.get_token(scope)
                return token.token
            except Exception:
                # Last resort: DefaultAzureCredential
                if self._credential is None:
                    self._credential = DefaultAzureCredential()
                token = self._credential.get_token(scope)
                return token.token

    def get_tenant_id(self) -> str:
        """
        Get the current tenant ID from Azure CLI.

        Returns:
            Tenant ID string
        """
        try:
            result = subprocess.run(
                ["az", "account", "show", "--query", "tenantId", "-o", "tsv"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception as e:
            raise RuntimeError(f"Failed to get tenant ID: {e}")

    def get_subscription_id(self) -> str:
        """
        Get the current subscription ID from Azure CLI.

        Returns:
            Subscription ID string
        """
        try:
            result = subprocess.run(
                ["az", "account", "show", "--query", "id", "-o", "tsv"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception as e:
            raise RuntimeError(f"Failed to get subscription ID: {e}")

    def get_user_object_id(self) -> str:
        """
        Get the current user's object ID from the access token claims.
        This avoids making network calls and works offline.

        Returns:
            User object ID string
        """
        try:
            # Get an access token - this uses cached credentials
            token = self.get_token("https://graph.microsoft.com/.default")
            
            # Decode the JWT token payload (middle part between the dots)
            # JWT format: header.payload.signature
            payload_part = token.split('.')[1]
            
            # Add padding if needed (JWT base64 may not be padded)
            padding = len(payload_part) % 4
            if padding:
                payload_part += '=' * (4 - padding)
            
            # Decode and parse the JSON payload
            decoded = base64.urlsafe_b64decode(payload_part)
            claims = json.loads(decoded)
            
            # The object ID is in the 'oid' claim
            if 'oid' in claims:
                return claims['oid']
            
            # Fallback: try the network call if token doesn't have OID
            result = subprocess.run(
                ["az", "ad", "signed-in-user", "show", "--query", "id", "-o", "tsv"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
            
        except Exception as e:
            raise RuntimeError(f"Failed to get user object ID: {e}")
