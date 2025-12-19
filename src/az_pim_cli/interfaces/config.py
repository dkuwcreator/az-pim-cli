"""Configuration protocol interface.

This module defines the protocol for configuration management.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Protocol


class ConfigProtocol(Protocol):
    """Protocol for configuration operations."""

    def get_alias(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get alias configuration by name.

        Args:
            name: Alias name

        Returns:
            Alias configuration or None
        """
        ...

    def add_alias(
        self,
        name: str,
        role: Optional[str] = None,
        duration: Optional[str] = None,
        justification: Optional[str] = None,
        scope: Optional[str] = None,
        subscription: Optional[str] = None,
        resource_group: Optional[str] = None,
        resource: Optional[str] = None,
        resource_type: Optional[str] = None,
        membership: Optional[str] = None,
        condition: Optional[str] = None,
    ) -> None:
        """Add or update an alias."""
        ...

    def remove_alias(self, name: str) -> bool:
        """Remove an alias."""
        ...

    def list_aliases(self) -> Dict[str, Dict[str, Any]]:
        """List all aliases."""
        ...

    def get_default(self, key: str, fallback: Optional[Any] = None) -> Any:
        """Get default configuration value."""
        ...

    def get_config_path(self) -> Path:
        """Get the configuration file path."""
        ...

    def save(self) -> None:
        """Save configuration to file."""
        ...
