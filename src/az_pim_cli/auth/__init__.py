"""Authentication module for az-pim-cli."""

# Re-export Azure SDK types for backward compatibility with tests
from azure.identity import AzureCliCredential, DefaultAzureCredential  # noqa: F401

from az_pim_cli.auth.azurecli import AzureAuth, ipv4_only_context, should_use_ipv4_only

__all__ = [
    "AzureAuth",
    "ipv4_only_context",
    "should_use_ipv4_only",
    "AzureCliCredential",
    "DefaultAzureCredential",
]
