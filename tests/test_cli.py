"""Tests for CLI commands."""

from typer.testing import CliRunner
from az_pim_cli.cli import app

runner = CliRunner()


def test_version_command() -> None:
    """Test version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "az-pim-cli" in result.stdout
    assert "0.1.0" in result.stdout


def test_alias_list_command() -> None:
    """Test alias list command."""
    result = runner.invoke(app, ["alias", "list"])
    # Should succeed even with no aliases
    assert result.exit_code == 0


def test_help_command() -> None:
    """Test help command."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Azure PIM CLI" in result.stdout


def test_list_help_shows_select_option() -> None:
    """Test that list help shows the --select option."""
    result = runner.invoke(app, ["list", "--help"])
    assert result.exit_code == 0
    # Check without colors (strip ANSI codes)
    assert "select" in result.stdout.lower()
    assert "interactive" in result.stdout.lower() or "activate a role" in result.stdout.lower()


def test_activate_help_shows_number_format() -> None:
    """Test that activate help shows role number format."""
    result = runner.invoke(app, ["activate", "--help"])
    assert result.exit_code == 0
    assert "number from list" in result.stdout.lower() or "#n" in result.stdout.lower()
