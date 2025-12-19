"""Configuration protocol interface.

This module defines the protocol for configuration management.
"""

from pathlib import Path
from typing import Any, Protocol


class ConfigProtocol(Protocol):
    """Protocol for configuration operations."""

    def get_alias(self, name: str) -> dict[str, Any] | None:
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
        role: str | None = None,
        duration: str | None = None,
        justification: str | None = None,
        scope: str | None = None,
        subscription: str | None = None,
        resource_group: str | None = None,
        resource: str | None = None,
        resource_type: str | None = None,
        membership: str | None = None,
        condition: str | None = None,
    ) -> None:
        """Add or update an alias."""
        ...

    def remove_alias(self, name: str) -> bool:
        """Remove an alias."""
        ...

    def list_aliases(self) -> dict[str, dict[str, Any]]:
        """List all aliases."""
        ...

    def get_default(self, key: str, fallback: Any | None = None) -> Any:
        """Get default configuration value."""
        ...

    def get_config_path(self) -> Path:
        """Get the configuration file path."""
        ...

    def save(self) -> None:
        """Save configuration to file."""
        ...
