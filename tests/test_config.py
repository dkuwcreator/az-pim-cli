"""Tests for Azure PIM CLI."""

from pathlib import Path

from az_pim_cli.config import Config


def test_config_initialization(tmp_path: Path) -> None:
    """Test config initialization."""
    config_path = tmp_path / "config.yml"
    config = Config(config_path)
    assert config.config_path == config_path


def test_add_and_get_alias(tmp_path: Path) -> None:
    """Test adding and retrieving an alias."""
    config_path = tmp_path / "config.yml"
    config = Config(config_path)

    config.add_alias(
        name="test-alias",
        role="Global Administrator",
        duration="PT8H",
        justification="Test justification",
        scope="directory",
    )

    alias = config.get_alias("test-alias")
    assert alias is not None
    assert alias["role"] == "Global Administrator"
    assert alias["duration"] == "PT8H"
    assert alias["justification"] == "Test justification"
    assert alias["scope"] == "directory"


def test_remove_alias(tmp_path: Path) -> None:
    """Test removing an alias."""
    config_path = tmp_path / "config.yml"
    config = Config(config_path)

    config.add_alias(name="test-alias", role="Test Role")
    assert config.get_alias("test-alias") is not None

    result = config.remove_alias("test-alias")
    assert result is True
    assert config.get_alias("test-alias") is None


def test_list_aliases(tmp_path: Path) -> None:
    """Test listing aliases."""
    config_path = tmp_path / "config.yml"
    config = Config(config_path)

    config.add_alias(name="alias1", role="Role 1")
    config.add_alias(name="alias2", role="Role 2")

    aliases = config.list_aliases()
    assert len(aliases) >= 2
    assert "alias1" in aliases
    assert "alias2" in aliases


def test_default_config(tmp_path: Path) -> None:
    """Test default configuration values."""
    config_path = tmp_path / "config.yml"
    config = Config(config_path)

    default_duration = config.get_default("duration")
    assert default_duration is not None

    default_justification = config.get_default("justification")
    assert default_justification is not None


def test_add_alias_with_extended_fields(tmp_path: Path) -> None:
    """Test adding an alias with extended fields."""
    config_path = tmp_path / "config.yml"
    config = Config(config_path)

    config.add_alias(
        name="extended-alias",
        role="Contributor",
        duration="PT4H",
        justification="Testing",
        scope="subscription",
        subscription="12345678-1234-1234-1234-123456789abc",
        resource="My Resource",
        resource_type="Microsoft.Compute/virtualMachines",
        membership="Direct",
        condition="@Resource[name] StringEquals 'vm1'",
    )

    alias = config.get_alias("extended-alias")
    assert alias is not None
    assert alias["role"] == "Contributor"
    assert alias["duration"] == "PT4H"
    assert alias["resource"] == "My Resource"
    assert alias["resource_type"] == "Microsoft.Compute/virtualMachines"
    assert alias["membership"] == "Direct"
    assert alias["condition"] == "@Resource[name] StringEquals 'vm1'"


def test_add_alias_without_required_fields(tmp_path: Path) -> None:
    """Test adding an alias without required fields (should work now)."""
    config_path = tmp_path / "config.yml"
    config = Config(config_path)

    # Should not raise an error - validation removed
    config.add_alias(
        name="partial-alias",
        duration="PT8H",
        justification="Testing partial alias",
    )

    alias = config.get_alias("partial-alias")
    assert alias is not None
    assert alias.get("duration") == "PT8H"
    assert alias.get("justification") == "Testing partial alias"
    assert alias.get("role") is None  # Not required anymore


def test_get_config_path(tmp_path: Path) -> None:
    """Test getting config file path."""
    config_path = tmp_path / "config.yml"
    config = Config(config_path)

    assert config.get_config_path() == config_path
