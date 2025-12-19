"""Enhanced configuration management with Pydantic validation.

This module provides typed configuration with Pydantic models,
supporting both YAML files and environment variables.

Environment Variables:
    AZ_PIM_IPV4_ONLY: Set to '1', 'true', or 'yes' to force IPv4-only DNS resolution.
    AZ_PIM_BACKEND: Choose API backend - 'ARM' (default) or 'GRAPH'.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AliasConfig(BaseModel):
    """Configuration for a role alias."""

    role: Optional[str] = None
    duration: Optional[str] = None
    justification: Optional[str] = None
    scope: Optional[str] = None
    subscription: Optional[str] = None
    resource_group: Optional[str] = None
    resource: Optional[str] = None
    resource_type: Optional[str] = None
    membership: Optional[str] = None
    condition: Optional[str] = None

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: Optional[str]) -> Optional[str]:
        """Validate ISO 8601 duration format."""
        if v and not v.startswith("PT"):
            # Allow simple hour format like "8" and convert to "PT8H"
            try:
                hours = int(v)
                return f"PT{hours}H"
            except ValueError:
                pass
        return v


class DefaultsConfig(BaseModel):
    """Default configuration values."""

    duration: str = Field(default="PT8H", description="Default duration for role activation")
    justification: str = Field(
        default="Requested via az-pim-cli", description="Default justification text"
    )
    fuzzy_matching: bool = Field(default=True, description="Enable fuzzy matching")
    fuzzy_threshold: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Minimum similarity for fuzzy matches"
    )
    cache_ttl_seconds: int = Field(
        default=300, ge=0, description="Cache TTL in seconds"
    )


class AppSettings(BaseSettings):
    """Application-level settings from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="AZ_PIM_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    ipv4_only: bool = Field(default=False, description="Force IPv4-only DNS resolution")
    backend: str = Field(default="ARM", description="API backend (ARM or GRAPH)")
    verbose: bool = Field(default=False, description="Enable verbose logging")

    @field_validator("backend")
    @classmethod
    def validate_backend(cls, v: str) -> str:
        """Validate backend choice."""
        v_upper = v.upper()
        if v_upper not in ("ARM", "GRAPH"):
            raise ValueError(f"Invalid backend: {v}. Must be 'ARM' or 'GRAPH'")
        return v_upper


class EnhancedConfig:
    """Enhanced configuration manager with Pydantic validation.

    This class provides backward compatibility with the original Config class
    while adding Pydantic-based validation and type safety.
    """

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

        # Load settings from environment
        self.settings = AppSettings()

        # Load file-based configuration
        self._aliases: Dict[str, AliasConfig] = {}
        self._defaults = DefaultsConfig()
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                raw_config = yaml.safe_load(f) or {}

            # Load aliases with validation
            raw_aliases = raw_config.get("aliases", {})
            for name, alias_data in raw_aliases.items():
                try:
                    self._aliases[name] = AliasConfig(**alias_data)
                except Exception as e:
                    # Skip invalid aliases but log a warning
                    print(f"Warning: Skipping invalid alias '{name}': {e}")

            # Load defaults with validation
            raw_defaults = raw_config.get("defaults", {})
            try:
                self._defaults = DefaultsConfig(**raw_defaults)
            except Exception as e:
                print(f"Warning: Using default configuration due to error: {e}")
                self._defaults = DefaultsConfig()
        else:
            # Create default configuration
            self._load_default_config()

    def _load_default_config(self) -> None:
        """Load default configuration."""
        self._aliases = {
            "example": AliasConfig(
                role="Global Administrator",
                duration="PT8H",
                justification="Administrative tasks",
                scope="directory",
            )
        }
        self._defaults = DefaultsConfig()

    def save(self) -> None:
        """Save configuration to YAML file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Convert to dict for YAML serialization
        config_dict = {
            "aliases": {
                name: alias.model_dump(exclude_none=True)
                for name, alias in self._aliases.items()
            },
            "defaults": self._defaults.model_dump(exclude_none=True),
        }

        with open(self.config_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False)

    def get_alias(self, name: str) -> Optional[Dict[str, Any]]:
        """Get alias configuration by name."""
        alias = self._aliases.get(name)
        return alias.model_dump(exclude_none=True) if alias else None

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
        """Add or update an alias with validation."""
        alias_config = AliasConfig(
            role=role,
            duration=duration,
            justification=justification,
            scope=scope,
            subscription=subscription,
            resource_group=resource_group,
            resource=resource,
            resource_type=resource_type,
            membership=membership,
            condition=condition,
        )
        self._aliases[name] = alias_config
        self.save()

    def remove_alias(self, name: str) -> bool:
        """Remove an alias."""
        if name in self._aliases:
            del self._aliases[name]
            self.save()
            return True
        return False

    def list_aliases(self) -> Dict[str, Dict[str, Any]]:
        """List all aliases."""
        return {
            name: alias.model_dump(exclude_none=True)
            for name, alias in self._aliases.items()
        }

    def get_default(self, key: str, fallback: Optional[Any] = None) -> Any:
        """Get default configuration value."""
        try:
            value = getattr(self._defaults, key)
            return value if value is not None else fallback
        except AttributeError:
            return fallback

    def get_config_path(self) -> Path:
        """Get the configuration file path."""
        return self.config_path
