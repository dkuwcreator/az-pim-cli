"""Configuration management for Azure PIM CLI.

Environment Variables:
    AZ_PIM_IPV4_ONLY: Set to '1', 'true', or 'yes' to force IPv4-only DNS resolution.
                      Useful for networks with IPv6 connectivity issues.

    AZ_PIM_BACKEND: Choose API backend - 'ARM' (default) or 'GRAPH'.
                    ARM backend aligns with Azure Portal and requires fewer permissions.
"""

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

        Note: In v2.0, aliases require prefixes to identify their command:
        - 'res:' for resource roles (azp-res)
        - 'entra:' for Entra directory roles (azp-entra)
        - 'groups:' for group memberships (azp-groups)

        Returns:
            Default configuration dictionary
        """
        return {
            "aliases": {
                "entra:example": {
                    "role": "Global Administrator",
                    "duration": "PT8H",
                    "justification": "Administrative tasks",
                    "scope": "directory",
                },
                "res:example": {
                    "role": "Owner",
                    "duration": "PT4H",
                    "justification": "Production deployment",
                    "scope": "subscriptions/YOUR_SUBSCRIPTION_ID",
                },
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
        """
        Add or update an alias.

        Args:
            name: Alias name
            role: Role name or ID (optional)
            duration: Duration string (optional)
            justification: Justification text (optional)
            scope: Scope (directory, subscription, resource) (optional)
            subscription: Subscription ID (for resource roles) (optional)
            resource_group: Resource group name (for resource roles) (optional)
            resource: Resource name (optional)
            resource_type: Resource type (optional)
            membership: Membership type (optional)
            condition: Condition expression (optional)
        """
        if "aliases" not in self._config:
            self._config["aliases"] = {}

        alias_config: Dict[str, Any] = {}
        if role:
            alias_config["role"] = role
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
        if resource:
            alias_config["resource"] = resource
        if resource_type:
            alias_config["resource_type"] = resource_type
        if membership:
            alias_config["membership"] = membership
        if condition:
            alias_config["condition"] = condition

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

    def list_aliases_by_prefix(self, prefix: str) -> Dict[str, Dict[str, Any]]:
        """
        List aliases with a specific prefix (e.g., 'res', 'entra', 'groups').

        Args:
            prefix: Prefix to filter aliases (e.g., 'res', 'entra', 'groups')

        Returns:
            Dictionary of aliases with the specified prefix
        """
        all_aliases = self._config.get("aliases", {})
        prefix_with_colon = f"{prefix}:"

        filtered_aliases = {}
        for alias_name, alias_config in all_aliases.items():
            if alias_name.startswith(prefix_with_colon):
                # Remove prefix for display
                short_name = alias_name[len(prefix_with_colon) :]
                filtered_aliases[short_name] = alias_config

        return filtered_aliases

    def get_default(self, key: str) -> Optional[Any]:
        """
        Get default configuration value.

        Args:
            key: Configuration key

        Returns:
            Configuration value or None
        """
        return self._config.get("defaults", {}).get(key)

    def get_config_path(self) -> Path:
        """
        Get the configuration file path.

        Returns:
            Path to the configuration file
        """
        return self.config_path
