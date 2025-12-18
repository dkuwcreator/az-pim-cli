"""Authentication module for Azure PIM CLI."""

import json
import subprocess
from typing import Optional

from azure.identity import DefaultAzureCredential, AzureCliCredential
from azure.core.credentials import AccessToken


class AzureAuth:
    """Handle Azure authentication using Azure CLI or MSAL."""

    def __init__(self) -> None:
        """Initialize Azure authentication."""
        self._credential: Optional[DefaultAzureCredential] = None
        self._cli_credential: Optional[AzureCliCredential] = None

    def get_token(self, scope: str = "https://management.azure.com/.default") -> str:
        """
        Get an access token for the specified scope.

        Args:
            scope: The scope for the access token

        Returns:
            Access token string
        """
        # Try Azure CLI first
        try:
            if self._cli_credential is None:
                self._cli_credential = AzureCliCredential()
            token = self._cli_credential.get_token(scope)
            return token.token
        except Exception:
            # Fall back to DefaultAzureCredential (includes MSAL)
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
        Get the current user's object ID.

        Returns:
            User object ID string
        """
        try:
            result = subprocess.run(
                ["az", "ad", "signed-in-user", "show", "--query", "id", "-o", "tsv"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception as e:
            raise RuntimeError(f"Failed to get user object ID: {e}")
