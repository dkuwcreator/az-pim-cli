"""Tests for CLI commands - split by PIM subject."""

from typer.testing import CliRunner

from az_pim_cli.cli import app_entra, app_groups, app_resources

runner = CliRunner()


# ============================================================================
# Test Resources CLI (azp-res)
# ============================================================================


class TestResourcesCLI:
    """Tests for azp-res (Azure resources) CLI."""

    def test_version_command(self) -> None:
        """Test version command."""
        result = runner.invoke(app_resources, ["version"])
        assert result.exit_code == 0
        assert "azp-res" in result.stdout
        assert "2.0.0" in result.stdout

    def test_help_command(self) -> None:
        """Test help command."""
        result = runner.invoke(app_resources, ["--help"])
        assert result.exit_code == 0
        assert "azp-res" in result.stdout or "Resources" in result.stdout

    def test_list_help(self) -> None:
        """Test list help command."""
        result = runner.invoke(app_resources, ["list", "--help"])
        assert result.exit_code == 0
        assert "list" in result.stdout.lower() or "eligible" in result.stdout.lower()

    def test_activate_help(self) -> None:
        """Test activate help command."""
        result = runner.invoke(app_resources, ["activate", "--help"])
        assert result.exit_code == 0
        assert "activate" in result.stdout.lower() or "role" in result.stdout.lower()


# ============================================================================
# Test Entra Roles CLI (azp-entra)
# ============================================================================


class TestEntraCLI:
    """Tests for azp-entra (Entra directory roles) CLI."""

    def test_version_command(self) -> None:
        """Test version command."""
        result = runner.invoke(app_entra, ["version"])
        assert result.exit_code == 0
        assert "azp-entra" in result.stdout
        assert "2.0.0" in result.stdout

    def test_help_command(self) -> None:
        """Test help command."""
        result = runner.invoke(app_entra, ["--help"])
        assert result.exit_code == 0
        assert "azp-entra" in result.stdout or "Entra" in result.stdout

    def test_list_help(self) -> None:
        """Test list help command."""
        result = runner.invoke(app_entra, ["list", "--help"])
        assert result.exit_code == 0
        assert "list" in result.stdout.lower() or "eligible" in result.stdout.lower()

    def test_activate_help(self) -> None:
        """Test activate help command."""
        result = runner.invoke(app_entra, ["activate", "--help"])
        assert result.exit_code == 0
        assert "activate" in result.stdout.lower() or "role" in result.stdout.lower()

    def test_history_help(self) -> None:
        """Test history help command."""
        result = runner.invoke(app_entra, ["history", "--help"])
        assert result.exit_code == 0
        assert "history" in result.stdout.lower()

    def test_approve_help(self) -> None:
        """Test approve help command."""
        result = runner.invoke(app_entra, ["approve", "--help"])
        assert result.exit_code == 0
        assert "approve" in result.stdout.lower()

    def test_pending_help(self) -> None:
        """Test pending help command."""
        result = runner.invoke(app_entra, ["pending", "--help"])
        assert result.exit_code == 0
        assert "pending" in result.stdout.lower()


# ============================================================================
# Test Groups CLI (azp-groups)
# ============================================================================


class TestGroupsCLI:
    """Tests for azp-groups (Entra group memberships) CLI."""

    def test_version_command(self) -> None:
        """Test version command."""
        result = runner.invoke(app_groups, ["version"])
        assert result.exit_code == 0
        assert "azp-groups" in result.stdout
        assert "2.0.0" in result.stdout

    def test_help_command(self) -> None:
        """Test help command."""
        result = runner.invoke(app_groups, ["--help"])
        assert result.exit_code == 0
        assert "azp-groups" in result.stdout or "Groups" in result.stdout

    def test_list_help(self) -> None:
        """Test list help command."""
        result = runner.invoke(app_groups, ["list", "--help"])
        assert result.exit_code == 0
        assert "list" in result.stdout.lower() or "eligible" in result.stdout.lower()

    def test_activate_help(self) -> None:
        """Test activate help command."""
        result = runner.invoke(app_groups, ["activate", "--help"])
        assert result.exit_code == 0
        assert "activate" in result.stdout.lower() or "group" in result.stdout.lower()

    def test_activate_access_option(self) -> None:
        """Test that activate shows access option."""
        result = runner.invoke(app_groups, ["activate", "--help"])
        assert result.exit_code == 0
        assert "access" in result.stdout.lower()
