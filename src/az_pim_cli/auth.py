"""Authentication module for Azure PIM CLI.

This module provides backward compatibility by re-exporting from the new auth structure.
See az_pim_cli.auth.azurecli for the actual implementation.
"""

# Backward compatibility: re-export from new structure
from az_pim_cli.auth.azurecli import (
    AzureAuth,
    ipv4_only_context,
    should_use_ipv4_only,
)

__all__ = ["AzureAuth", "ipv4_only_context", "should_use_ipv4_only"]
