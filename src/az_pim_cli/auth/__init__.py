"""Authentication module for az-pim-cli."""

from az_pim_cli.auth.azurecli import AzureAuth, ipv4_only_context, should_use_ipv4_only

# Re-export Azure SDK types for backward compatibility with tests
from azure.identity import AzureCliCredential, DefaultAzureCredential  # noqa: F401

__all__ = [
    "AzureAuth",
    "ipv4_only_context",
    "should_use_ipv4_only",
    "AzureCliCredential",
    "DefaultAzureCredential",
]
