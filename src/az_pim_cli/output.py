"""Rich output formatting for az-pim-cli.

This module provides standardized Rich table and panel formatting for
consistent, beautiful terminal output.

Reference:
- https://rich.readthedocs.io/en/stable/tables.html
- https://rich.readthedocs.io/en/stable/introduction.html
"""

from rich.panel import Panel
from rich.table import Table

from az_pim_cli.console import console


def create_roles_table(
    title: str = "Roles",
    show_scope: bool = False,
    show_status: bool = True,
    full_scope: bool = False,
) -> Table:
    """
    Create a Rich table for displaying roles.

    Args:
        title: Table title
        show_scope: Whether to include scope column
        show_status: Whether to include status column
        full_scope: Whether to show full scope paths

    Returns:
        Configured Rich Table
    """
    table = Table(title=title, show_header=True, header_style="bold cyan")

    table.add_column("#", style="dim", width=4)
    table.add_column("Role Name", style="green")

    if show_status:
        table.add_column("Status", style="yellow")

    if show_scope:
        table.add_column("Scope", style="blue")

    table.add_column("Role ID", style="dim", overflow="fold")

    return table


def create_history_table(title: str = "Activation History") -> Table:
    """
    Create a Rich table for displaying activation history.

    Args:
        title: Table title

    Returns:
        Configured Rich Table
    """
    table = Table(title=title, show_header=True, header_style="bold cyan")

    table.add_column("Date", style="cyan")
    table.add_column("Role", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Duration", style="blue")
    table.add_column("Justification", overflow="fold")

    return table


def create_approvals_table(title: str = "Pending Approvals") -> Table:
    """
    Create a Rich table for displaying pending approvals.

    Args:
        title: Table title

    Returns:
        Configured Rich Table
    """
    table = Table(title=title, show_header=True, header_style="bold cyan")

    table.add_column("#", style="dim", width=4)
    table.add_column("Requestor", style="green")
    table.add_column("Role", style="cyan")
    table.add_column("Requested", style="blue")
    table.add_column("Justification", overflow="fold")
    table.add_column("Request ID", style="dim", overflow="fold")

    return table


def print_success(message: str) -> None:
    """
    Print a success message in a green panel.

    Args:
        message: Success message to display
    """
    console.print(Panel(message, style="green", title="✓ Success"))


def print_error(message: str, detail: str | None = None) -> None:
    """
    Print an error message in a red panel.

    Args:
        message: Error message to display
        detail: Optional detailed error information
    """
    if detail:
        full_message = f"{message}\n\n[dim]{detail}[/dim]"
    else:
        full_message = message

    console.print(Panel(full_message, style="red", title="✗ Error"))


def print_warning(message: str) -> None:
    """
    Print a warning message in a yellow panel.

    Args:
        message: Warning message to display
    """
    console.print(Panel(message, style="yellow", title="⚠ Warning"))


def print_info(message: str) -> None:
    """
    Print an informational message in a blue panel.

    Args:
        message: Info message to display
    """
    console.print(Panel(message, style="blue", title="ℹ Info"))


def format_duration(duration_str: str) -> str:
    """
    Format ISO 8601 duration to human-readable format.

    Args:
        duration_str: ISO 8601 duration (e.g., PT8H, PT2H30M)

    Returns:
        Human-readable duration (e.g., "8 hours", "2h 30m")
    """
    if not duration_str or not duration_str.startswith("PT"):
        return duration_str

    # Remove PT prefix
    duration = duration_str[2:]

    parts = []
    if "H" in duration:
        hours = duration.split("H")[0]
        parts.append(f"{hours}h")
        duration = duration.split("H")[1] if "H" in duration else ""

    if "M" in duration:
        minutes = duration.split("M")[0]
        parts.append(f"{minutes}m")

    return " ".join(parts) if parts else duration_str


def format_datetime(dt_str: str | None) -> str:
    """
    Format ISO 8601 datetime to human-readable format.

    Args:
        dt_str: ISO 8601 datetime string

    Returns:
        Formatted datetime string
    """
    if not dt_str:
        return "N/A"

    try:
        from datetime import datetime

        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, AttributeError):
        return dt_str


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix
