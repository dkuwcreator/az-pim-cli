"""Results tables and summaries for az-pim-cli.

This module provides enhanced table rendering with consistent styling
for displaying results in a structured, readable format.

Reference:
- https://rich.readthedocs.io/en/stable/tables.html
"""

from typing import Any

from rich.table import Table

from az_pim_cli.console import console


def create_summary_table(
    title: str,
    *,
    show_header: bool = True,
    header_style: str = "bold magenta",
    border_style: str = "blue",
) -> Table:
    """
    Create a styled table for summary information.

    Args:
        title: Table title
        show_header: Whether to show table header (default: True)
        header_style: Style for header row (default: "bold magenta")
        border_style: Style for table border (default: "blue")

    Returns:
        Configured Rich Table
    """
    return Table(
        title=title,
        show_header=show_header,
        header_style=header_style,
        border_style=border_style,
        show_lines=False,
        padding=(0, 1),
    )


def create_role_summary_table(title: str = "Role Summary") -> Table:
    """
    Create a standardized table for role summaries.

    Args:
        title: Table title

    Returns:
        Configured Rich Table with role columns
    """
    table = create_summary_table(title)
    table.add_column("#", style="bold white", justify="right", width=4)
    table.add_column("Role", style="cyan", no_wrap=False)
    table.add_column("Status", style="green")
    table.add_column("Scope", style="dim", no_wrap=False)
    table.add_column("End Time", style="yellow")
    return table


def create_activation_summary_table(title: str = "Activation Summary") -> Table:
    """
    Create a standardized table for activation summaries.

    Args:
        title: Table title

    Returns:
        Configured Rich Table with activation columns
    """
    table = create_summary_table(title)
    table.add_column("Role", style="cyan")
    table.add_column("Duration", style="green")
    table.add_column("Justification", style="dim", no_wrap=False)
    table.add_column("Status", style="yellow")
    table.add_column("Requested", style="dim")
    return table


def create_key_value_table(title: str | None = None) -> Table:
    """
    Create a simple key-value table for displaying configuration or metadata.

    Args:
        title: Optional table title

    Returns:
        Configured Rich Table with Key and Value columns
    """
    table = create_summary_table(title or "Details", show_header=False)
    table.add_column("Key", style="bold", no_wrap=True)
    table.add_column("Value", style="cyan", no_wrap=False)
    return table


def print_summary(data: dict[str, Any], title: str = "Summary") -> None:
    """
    Print a dictionary as a formatted key-value table.

    Args:
        data: Dictionary of key-value pairs to display
        title: Table title
    """
    table = create_key_value_table(title)
    for key, value in data.items():
        table.add_row(key, str(value))
    console.print(table)


def print_role_status_summary(
    total_roles: int,
    active_roles: int,
    eligible_roles: int,
    *,
    title: str = "Role Status Summary",
) -> None:
    """
    Print a summary of role statuses.

    Args:
        total_roles: Total number of roles
        active_roles: Number of currently active roles
        eligible_roles: Number of eligible roles
        title: Table title
    """
    table = create_key_value_table(title)
    table.add_row("Total Roles", str(total_roles))
    table.add_row("Active", f"[green]{active_roles}[/green]")
    table.add_row("Eligible", f"[yellow]{eligible_roles}[/yellow]")
    console.print(table)
