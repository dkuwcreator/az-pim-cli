"""Tests for report module."""

from unittest.mock import patch

from rich.table import Table

from az_pim_cli.report import (
    create_activation_summary_table,
    create_key_value_table,
    create_role_summary_table,
    create_summary_table,
    print_role_status_summary,
    print_summary,
)


class TestCreateSummaryTable:
    """Tests for create_summary_table function."""

    def test_create_summary_table_basic(self):
        """Test creating a basic summary table."""
        table = create_summary_table("Test Summary")
        assert isinstance(table, Table)
        assert table.title == "Test Summary"

    def test_create_summary_table_no_header(self):
        """Test creating summary table without header."""
        table = create_summary_table("Test", show_header=False)
        assert isinstance(table, Table)
        assert table.show_header is False

    def test_create_summary_table_custom_styles(self):
        """Test creating summary table with custom styles."""
        table = create_summary_table("Test", header_style="bold green", border_style="red")
        assert isinstance(table, Table)


class TestCreateRoleSummaryTable:
    """Tests for create_role_summary_table function."""

    def test_create_role_summary_table_default(self):
        """Test creating role summary table with default title."""
        table = create_role_summary_table()
        assert isinstance(table, Table)
        assert table.title == "Role Summary"

    def test_create_role_summary_table_custom_title(self):
        """Test creating role summary table with custom title."""
        table = create_role_summary_table(title="Custom Roles")
        assert isinstance(table, Table)
        assert table.title == "Custom Roles"


class TestCreateActivationSummaryTable:
    """Tests for create_activation_summary_table function."""

    def test_create_activation_summary_table_default(self):
        """Test creating activation summary table with default title."""
        table = create_activation_summary_table()
        assert isinstance(table, Table)
        assert table.title == "Activation Summary"

    def test_create_activation_summary_table_custom_title(self):
        """Test creating activation summary table with custom title."""
        table = create_activation_summary_table(title="Recent Activations")
        assert isinstance(table, Table)
        assert table.title == "Recent Activations"


class TestCreateKeyValueTable:
    """Tests for create_key_value_table function."""

    def test_create_key_value_table_default(self):
        """Test creating key-value table with default title."""
        table = create_key_value_table()
        assert isinstance(table, Table)
        assert table.title == "Details"

    def test_create_key_value_table_custom_title(self):
        """Test creating key-value table with custom title."""
        table = create_key_value_table(title="Configuration")
        assert isinstance(table, Table)
        assert table.title == "Configuration"

    def test_create_key_value_table_no_header(self):
        """Test that key-value table has no header by default."""
        table = create_key_value_table()
        assert table.show_header is False


class TestPrintSummary:
    """Tests for print_summary function."""

    @patch("az_pim_cli.report.console")
    def test_print_summary_basic(self, mock_console):
        """Test printing a basic summary."""
        data = {"Name": "Test", "Value": "123", "Status": "Active"}
        print_summary(data)

        mock_console.print.assert_called_once()

    @patch("az_pim_cli.report.console")
    def test_print_summary_custom_title(self, mock_console):
        """Test printing summary with custom title."""
        data = {"Key": "Value"}
        print_summary(data, title="Custom Title")

        mock_console.print.assert_called_once()

    @patch("az_pim_cli.report.console")
    def test_print_summary_empty_dict(self, mock_console):
        """Test printing empty summary."""
        print_summary({})

        mock_console.print.assert_called_once()


class TestPrintRoleStatusSummary:
    """Tests for print_role_status_summary function."""

    @patch("az_pim_cli.report.console")
    def test_print_role_status_summary_basic(self, mock_console):
        """Test printing role status summary."""
        print_role_status_summary(total_roles=10, active_roles=3, eligible_roles=7)

        mock_console.print.assert_called_once()

    @patch("az_pim_cli.report.console")
    def test_print_role_status_summary_custom_title(self, mock_console):
        """Test printing role status summary with custom title."""
        print_role_status_summary(total_roles=5, active_roles=2, eligible_roles=3, title="My Roles")

        mock_console.print.assert_called_once()

    @patch("az_pim_cli.report.console")
    def test_print_role_status_summary_zero_roles(self, mock_console):
        """Test printing role status summary with zero roles."""
        print_role_status_summary(total_roles=0, active_roles=0, eligible_roles=0)

        mock_console.print.assert_called_once()
