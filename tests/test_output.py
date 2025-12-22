"""Tests for output formatting utilities."""

from unittest.mock import patch

from rich.table import Table

from az_pim_cli.output import (
    create_approvals_table,
    create_history_table,
    create_roles_table,
    format_datetime,
    format_duration,
    print_error,
    print_info,
    print_success,
    print_warning,
    truncate_text,
)


class TestFormatDuration:
    """Tests for format_duration function."""

    def test_format_duration_hours(self):
        """Test formatting ISO 8601 duration with hours."""
        result = format_duration("PT2H")
        assert result == "2h"

    def test_format_duration_hours_and_minutes(self):
        """Test formatting ISO 8601 duration with hours and minutes."""
        result = format_duration("PT2H30M")
        assert result == "2h 30m"

    def test_format_duration_minutes_only(self):
        """Test formatting duration with only minutes."""
        result = format_duration("PT45M")
        assert result == "45m"

    def test_format_duration_invalid(self):
        """Test formatting invalid duration returns original."""
        result = format_duration("invalid")
        assert result == "invalid"

    def test_format_duration_empty(self):
        """Test formatting empty duration returns original."""
        result = format_duration("")
        assert result == ""


class TestFormatDatetime:
    """Tests for format_datetime function."""

    def test_format_datetime_string(self):
        """Test formatting datetime from ISO string."""
        dt_str = "2024-01-15T10:30:00Z"
        result = format_datetime(dt_str)
        assert "2024-01-15" in result
        assert "10:30" in result

    def test_format_datetime_with_plus_timezone(self):
        """Test formatting datetime with +00:00 timezone."""
        dt_str = "2024-01-15T10:30:00+00:00"
        result = format_datetime(dt_str)
        assert "2024-01-15" in result

    def test_format_datetime_invalid(self):
        """Test formatting invalid datetime returns original."""
        invalid = "not-a-date"
        result = format_datetime(invalid)
        assert result == invalid

    def test_format_datetime_none(self):
        """Test formatting None datetime returns N/A."""
        result = format_datetime(None)
        assert result == "N/A"


class TestTruncateText:
    """Tests for truncate_text function."""

    def test_truncate_text_short(self):
        """Test text shorter than max length is not truncated."""
        result = truncate_text("short text", max_length=50)
        assert result == "short text"

    def test_truncate_text_long(self):
        """Test text longer than max length is truncated."""
        long_text = "This is a very long text that should be truncated"
        result = truncate_text(long_text, max_length=20)
        assert len(result) == 20
        assert result.endswith("...")

    def test_truncate_text_custom_suffix(self):
        """Test truncation with custom suffix."""
        long_text = "This is a very long text"
        result = truncate_text(long_text, max_length=15, suffix=">>")
        assert result.endswith(">>")


class TestCreateRolesTable:
    """Tests for create_roles_table function."""

    def test_create_roles_table_basic(self):
        """Test creating a basic roles table."""
        table = create_roles_table()
        assert isinstance(table, Table)
        assert table.title == "Roles"

    def test_create_roles_table_with_scope(self):
        """Test creating roles table with scope column."""
        table = create_roles_table(show_scope=True)
        assert isinstance(table, Table)

    def test_create_roles_table_without_status(self):
        """Test creating roles table without status column."""
        table = create_roles_table(show_status=False)
        assert isinstance(table, Table)


class TestCreateHistoryTable:
    """Tests for create_history_table function."""

    def test_create_history_table(self):
        """Test creating a history table."""
        table = create_history_table()
        assert isinstance(table, Table)
        assert table.title == "Activation History"

    def test_create_history_table_custom_title(self):
        """Test creating history table with custom title."""
        table = create_history_table(title="Custom History")
        assert isinstance(table, Table)
        assert table.title == "Custom History"


class TestCreateApprovalsTable:
    """Tests for create_approvals_table function."""

    def test_create_approvals_table(self):
        """Test creating an approvals table."""
        table = create_approvals_table()
        assert isinstance(table, Table)
        assert table.title == "Pending Approvals"

    def test_create_approvals_table_custom_title(self):
        """Test creating approvals table with custom title."""
        table = create_approvals_table(title="Custom Approvals")
        assert isinstance(table, Table)
        assert table.title == "Custom Approvals"


class TestPrintFunctions:
    """Tests for print functions."""

    @patch("az_pim_cli.output.console")
    def test_print_success(self, mock_console):
        """Test print_success function."""
        print_success("Success message")
        mock_console.print.assert_called_once()

    @patch("az_pim_cli.output.console")
    def test_print_error(self, mock_console):
        """Test print_error function."""
        print_error("Error message")
        mock_console.print.assert_called_once()

    @patch("az_pim_cli.output.console")
    def test_print_error_with_detail(self, mock_console):
        """Test print_error function with detail."""
        print_error("Error message", detail="Error details")
        mock_console.print.assert_called_once()

    @patch("az_pim_cli.output.console")
    def test_print_warning(self, mock_console):
        """Test print_warning function."""
        print_warning("Warning message")
        mock_console.print.assert_called_once()

    @patch("az_pim_cli.output.console")
    def test_print_info(self, mock_console):
        """Test print_info function."""
        print_info("Info message")
        mock_console.print.assert_called_once()
