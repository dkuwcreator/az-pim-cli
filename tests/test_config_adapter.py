"""Tests for configuration adapter."""

import tempfile
from pathlib import Path

import pytest

from az_pim_cli.infra.config_adapter import AliasConfig, DefaultsConfig, EnhancedConfig


def test_enhanced_config_initialization():
    """Test that EnhancedConfig initializes correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yml"
        config = EnhancedConfig(config_path=config_path)

        assert config.config_path == config_path
        assert isinstance(config._defaults, DefaultsConfig)
        assert isinstance(config._aliases, dict)


def test_alias_config_validation():
    """Test that AliasConfig validates duration format."""
    # Valid PT format
    alias1 = AliasConfig(role="Owner", duration="PT8H")
    assert alias1.duration == "PT8H"

    # Simple hour format should be converted
    alias2 = AliasConfig(role="Contributor", duration="4")
    assert alias2.duration == "PT4H"

    # Invalid format should be kept as-is
    alias3 = AliasConfig(role="Reader", duration="invalid")
    assert alias3.duration == "invalid"


def test_defaults_config_validation():
    """Test that DefaultsConfig validates properly."""
    defaults = DefaultsConfig(
        duration="PT4H",
        fuzzy_matching=True,
        fuzzy_threshold=0.9,
        cache_ttl_seconds=600,
    )

    assert defaults.duration == "PT4H"
    assert defaults.fuzzy_matching is True
    assert defaults.fuzzy_threshold == 0.9
    assert defaults.cache_ttl_seconds == 600

    # Test validation bounds
    with pytest.raises(ValueError):
        DefaultsConfig(fuzzy_threshold=1.5)  # Must be <= 1.0


def test_enhanced_config_add_alias():
    """Test adding an alias with validation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yml"
        config = EnhancedConfig(config_path=config_path)

        config.add_alias(
            name="test-alias",
            role="Contributor",
            duration="4",  # Should be converted to PT4H
            justification="Testing",
            scope="subscription",
        )

        alias = config.get_alias("test-alias")
        assert alias is not None
        assert alias["role"] == "Contributor"
        assert alias["duration"] == "PT4H"
        assert alias["justification"] == "Testing"


def test_enhanced_config_backward_compatibility():
    """Test that EnhancedConfig maintains backward compatibility."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yml"
        config = EnhancedConfig(config_path=config_path)

        # Test backward compatible methods
        config.add_alias("test", role="Owner")
        assert config.get_alias("test") is not None

        aliases = config.list_aliases()
        assert "test" in aliases

        assert config.remove_alias("test") is True
        assert config.get_alias("test") is None

        # Test get_default
        assert config.get_default("duration") == "PT8H"
        assert config.get_default("nonexistent", "fallback") == "fallback"

        # Test get_config_path
        assert config.get_config_path() == config_path


def test_enhanced_config_save_load():
    """Test saving and loading configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yml"

        # Create and save config
        config1 = EnhancedConfig(config_path=config_path)
        config1.add_alias(
            name="prod",
            role="Contributor",
            duration="PT4H",
            scope="subscription",
        )
        config1.save()

        # Load config
        config2 = EnhancedConfig(config_path=config_path)
        alias = config2.get_alias("prod")
        assert alias is not None
        assert alias["role"] == "Contributor"
        assert alias["duration"] == "PT4H"
