"""Configuration management for Azure PIM CLI."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class Config:
    """Manage configuration and aliases."""

    DEFAULT_CONFIG_DIR = Path.home() / ".az-pim-cli"
    DEFAULT_CONFIG_FILE = "config.yml"

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """
        Initialize configuration.

        Args:
            config_path: Optional path to config file
        """
        if config_path is None:
            self.config_dir = self.DEFAULT_CONFIG_DIR
            self.config_path = self.config_dir / self.DEFAULT_CONFIG_FILE
        else:
            self.config_path = config_path
            self.config_dir = config_path.parent

        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file."""
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration.

        Returns:
            Default configuration dictionary
        """
        return {
            "aliases": {
                "example": {
                    "role": "Global Administrator",
                    "duration": "PT8H",
                    "justification": "Administrative tasks",
                    "scope": "directory",
                }
            },
            "defaults": {"duration": "PT8H", "justification": "Requested via az-pim-cli"},
        }

    def save(self) -> None:
        """Save configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(self._config, f, default_flow_style=False)

    def get_alias(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get alias configuration by name.

        Args:
            name: Alias name

        Returns:
            Alias configuration or None
        """
        return self._config.get("aliases", {}).get(name)

    def add_alias(
        self,
        name: str,
        role: str,
        duration: Optional[str] = None,
        justification: Optional[str] = None,
        scope: Optional[str] = None,
        subscription: Optional[str] = None,
        resource_group: Optional[str] = None,
    ) -> None:
        """
        Add or update an alias.

        Args:
            name: Alias name
            role: Role name or ID
            duration: Duration string
            justification: Justification text
            scope: Scope (directory, subscription, resource)
            subscription: Subscription ID (for resource roles)
            resource_group: Resource group name (for resource roles)
        """
        if "aliases" not in self._config:
            self._config["aliases"] = {}

        alias_config = {"role": role}
        if duration:
            alias_config["duration"] = duration
        if justification:
            alias_config["justification"] = justification
        if scope:
            alias_config["scope"] = scope
        if subscription:
            alias_config["subscription"] = subscription
        if resource_group:
            alias_config["resource_group"] = resource_group

        self._config["aliases"][name] = alias_config
        self.save()

    def remove_alias(self, name: str) -> bool:
        """
        Remove an alias.

        Args:
            name: Alias name

        Returns:
            True if removed, False if not found
        """
        if name in self._config.get("aliases", {}):
            del self._config["aliases"][name]
            self.save()
            return True
        return False

    def list_aliases(self) -> Dict[str, Dict[str, Any]]:
        """
        List all aliases.

        Returns:
            Dictionary of aliases
        """
        return self._config.get("aliases", {})

    def get_default(self, key: str) -> Optional[Any]:
        """
        Get default configuration value.

        Args:
            key: Configuration key

        Returns:
            Configuration value or None
        """
        return self._config.get("defaults", {}).get(key)
