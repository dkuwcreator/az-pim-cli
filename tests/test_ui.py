"""Tests for UI helper functions."""

from unittest.mock import patch

from rich.text import Text

from az_pim_cli.ui import (
    error,
    info,
    print_key_value,
    print_list,
    section,
    separator,
    status_badge,
    success,
    warn,
)


class TestSection:
    """Tests for section function."""

    @patch("az_pim_cli.ui.console")
    def test_section_default_style(self, mock_console):
        """Test section with default style."""
        section("Test Section")

        mock_console.print.assert_called_once()
        args = mock_console.print.call_args[0]
        assert "Test Section" in args[0]
        assert "═══" in args[0]

    @patch("az_pim_cli.ui.console")
    def test_section_custom_style(self, mock_console):
        """Test section with custom style."""
        section("Custom Section", style="bold yellow")

        mock_console.print.assert_called_once()
        args = mock_console.print.call_args[0]
        assert "Custom Section" in args[0]


class TestInfo:
    """Tests for info function."""

    @patch("az_pim_cli.ui.console")
    def test_info_default(self, mock_console):
        """Test info with default parameters."""
        info("Test info message")

        mock_console.print.assert_called_once()

    @patch("az_pim_cli.ui.console")
    def test_info_custom_title(self, mock_console):
        """Test info with custom title."""
        info("Test message", title="Custom Title")

        mock_console.print.assert_called_once()

    @patch("az_pim_cli.ui.console")
    def test_info_custom_emoji(self, mock_console):
        """Test info with custom emoji."""
        info("Test message", emoji="🔔")

        mock_console.print.assert_called_once()


class TestSuccess:
    """Tests for success function."""

    @patch("az_pim_cli.ui.console")
    def test_success_default(self, mock_console):
        """Test success with default parameters."""
        success("Operation successful")

        mock_console.print.assert_called_once()

    @patch("az_pim_cli.ui.console")
    def test_success_custom_title(self, mock_console):
        """Test success with custom title."""
        success("Operation successful", title="Great!")

        mock_console.print.assert_called_once()


class TestWarn:
    """Tests for warn function."""

    @patch("az_pim_cli.ui.console")
    def test_warn_default(self, mock_console):
        """Test warn with default parameters."""
        warn("Warning message")

        mock_console.print.assert_called_once()

    @patch("az_pim_cli.ui.console")
    def test_warn_custom_emoji(self, mock_console):
        """Test warn with custom emoji."""
        warn("Warning message", emoji="⚡")

        mock_console.print.assert_called_once()


class TestError:
    """Tests for error function."""

    @patch("az_pim_cli.ui.console")
    def test_error_simple(self, mock_console):
        """Test error with simple message."""
        error("Error occurred")

        mock_console.print.assert_called_once()

    @patch("az_pim_cli.ui.console")
    def test_error_with_detail(self, mock_console):
        """Test error with detail."""
        error("Error occurred", detail="Detailed error information")

        mock_console.print.assert_called_once()

    @patch("az_pim_cli.ui.console")
    def test_error_custom_title(self, mock_console):
        """Test error with custom title."""
        error("Error occurred", title="Fatal Error")

        mock_console.print.assert_called_once()


class TestPrintKeyValue:
    """Tests for print_key_value function."""

    @patch("az_pim_cli.ui.console")
    def test_print_key_value_default(self, mock_console):
        """Test print_key_value with default styles."""
        print_key_value("Name", "Value")

        mock_console.print.assert_called_once()
        args = mock_console.print.call_args[0]
        assert "Name" in args[0]
        assert "Value" in args[0]

    @patch("az_pim_cli.ui.console")
    def test_print_key_value_custom_styles(self, mock_console):
        """Test print_key_value with custom styles."""
        print_key_value("Key", "Val", key_style="yellow", value_style="green")

        mock_console.print.assert_called_once()


class TestPrintList:
    """Tests for print_list function."""

    @patch("az_pim_cli.ui.console")
    def test_print_list_default(self, mock_console):
        """Test print_list with default bullet."""
        items = ["Item 1", "Item 2", "Item 3"]
        print_list(items)

        assert mock_console.print.call_count == 3

    @patch("az_pim_cli.ui.console")
    def test_print_list_custom_bullet(self, mock_console):
        """Test print_list with custom bullet."""
        items = ["Item 1", "Item 2"]
        print_list(items, bullet="→")

        assert mock_console.print.call_count == 2

    @patch("az_pim_cli.ui.console")
    def test_print_list_empty(self, mock_console):
        """Test print_list with empty list."""
        print_list([])

        mock_console.print.assert_not_called()


class TestStatusBadge:
    """Tests for status_badge function."""

    def test_status_badge_info(self):
        """Test status badge with info status."""
        badge = status_badge("INFO", status="info")
        assert isinstance(badge, Text)

    def test_status_badge_success(self):
        """Test status badge with success status."""
        badge = status_badge("ACTIVE", status="success")
        assert isinstance(badge, Text)

    def test_status_badge_warning(self):
        """Test status badge with warning status."""
        badge = status_badge("WARNING", status="warning")
        assert isinstance(badge, Text)

    def test_status_badge_error(self):
        """Test status badge with error status."""
        badge = status_badge("ERROR", status="error")
        assert isinstance(badge, Text)

    def test_status_badge_default(self):
        """Test status badge with default status."""
        badge = status_badge("DEFAULT")
        assert isinstance(badge, Text)


class TestSeparator:
    """Tests for separator function."""

    @patch("az_pim_cli.ui.console")
    def test_separator_default(self, mock_console):
        """Test separator with default character."""
        mock_console.width = 80
        separator()

        mock_console.print.assert_called_once()
        args = mock_console.print.call_args[0]
        assert "─" in args[0]

    @patch("az_pim_cli.ui.console")
    def test_separator_custom_char(self, mock_console):
        """Test separator with custom character."""
        mock_console.width = 80
        separator(char="=")

        mock_console.print.assert_called_once()
        args = mock_console.print.call_args[0]
        assert "=" in args[0]
