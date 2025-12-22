"""UI helper functions for az-pim-cli.

This module provides standardized UI helpers using Rich styling, panels,
and headings for consistent, readable terminal output.

Reference:
- https://rich.readthedocs.io/en/stable/panel.html
- https://rich.readthedocs.io/en/stable/text.html
"""

from typing import Any

from rich.panel import Panel
from rich.text import Text

from az_pim_cli.console import console


def section(title: str, *, style: str = "bold cyan") -> None:
    """
    Print a section heading to visually separate different parts of output.

    Args:
        title: Section title text
        style: Rich style for the title (default: "bold cyan")
    """
    console.print(f"\n[{style}]═══ {title} ═══[/{style}]\n")


def info(message: str, *, title: str | None = None, emoji: str = "ℹ") -> None:
    """
    Print an informational message in a blue panel.

    Args:
        message: Info message to display
        title: Optional panel title (default: "ℹ Info")
        emoji: Emoji to use in title (default: "ℹ")
    """
    panel_title = title or f"{emoji} Info"
    console.print(Panel(message, style="blue", title=panel_title, border_style="blue"))


def success(message: str, *, title: str | None = None, emoji: str = "✓") -> None:
    """
    Print a success message in a green panel.

    Args:
        message: Success message to display
        title: Optional panel title (default: "✓ Success")
        emoji: Emoji to use in title (default: "✓")
    """
    panel_title = title or f"{emoji} Success"
    console.print(Panel(message, style="green", title=panel_title, border_style="green"))


def warn(message: str, *, title: str | None = None, emoji: str = "⚠") -> None:
    """
    Print a warning message in a yellow panel.

    Args:
        message: Warning message to display
        title: Optional panel title (default: "⚠ Warning")
        emoji: Emoji to use in title (default: "⚠")
    """
    panel_title = title or f"{emoji} Warning"
    console.print(Panel(message, style="yellow", title=panel_title, border_style="yellow"))


def error(message: str, *, detail: str | None = None, title: str | None = None, emoji: str = "✗") -> None:
    """
    Print an error message in a red panel.

    Args:
        message: Error message to display
        detail: Optional detailed error information
        title: Optional panel title (default: "✗ Error")
        emoji: Emoji to use in title (default: "✗")
    """
    panel_title = title or f"{emoji} Error"
    if detail:
        full_message = f"{message}\n\n[dim]{detail}[/dim]"
    else:
        full_message = message

    console.print(Panel(full_message, style="red", title=panel_title, border_style="red"))


def print_key_value(key: str, value: Any, *, key_style: str = "bold", value_style: str = "cyan") -> None:
    """
    Print a key-value pair with consistent formatting.

    Args:
        key: The key/label
        value: The value
        key_style: Rich style for the key (default: "bold")
        value_style: Rich style for the value (default: "cyan")
    """
    console.print(f"[{key_style}]{key}:[/{key_style}] [{value_style}]{value}[/{value_style}]")


def print_list(items: list[str], *, bullet: str = "•", style: str = "cyan") -> None:
    """
    Print a bulleted list of items.

    Args:
        items: List of items to print
        bullet: Bullet character (default: "•")
        style: Rich style for items (default: "cyan")
    """
    for item in items:
        console.print(f"  [{style}]{bullet}[/{style}] {item}")


def status_badge(text: str, *, status: str = "info") -> Text:
    """
    Create a styled status badge.

    Args:
        text: Badge text
        status: Badge type - "info", "success", "warning", "error", "active" (default: "info")

    Returns:
        Rich Text object with styled badge
    """
    status_styles = {
        "info": ("blue", "on blue"),
        "success": ("green", "on green"),
        "warning": ("yellow", "on yellow"),
        "error": ("red", "on red"),
        "active": ("green", "on green"),
        "inactive": ("dim", "on dim"),
    }

    fg_style, bg_style = status_styles.get(status, status_styles["info"])
    badge = Text(f" {text} ", style=f"bold {fg_style}")
    return badge


def separator(*, char: str = "─", style: str = "dim") -> None:
    """
    Print a horizontal separator line.

    Args:
        char: Character to use for separator (default: "─")
        style: Rich style for the separator (default: "dim")
    """
    # Auto-adjust to console width
    width = console.width
    console.print(f"[{style}]{char * width}[/{style}]")
