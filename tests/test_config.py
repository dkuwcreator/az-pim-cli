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
