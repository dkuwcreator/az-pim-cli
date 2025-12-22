"""Shared Rich console for az-pim-cli.

This module provides a centralized Console instance and Rich traceback configuration
for consistent, beautiful terminal output across the entire CLI.

Reference:
- https://rich.readthedocs.io/en/stable/console.html
- https://rich.readthedocs.io/en/stable/traceback.html
"""

from rich.console import Console
from rich.traceback import install as install_rich_traceback

# Shared console instance - auto-detects width and color support
console = Console()


def install_traceback(show_locals: bool = False) -> None:
    """
    Install Rich traceback handler for beautiful error displays.

    Args:
        show_locals: Whether to show local variables in tracebacks (default: False)
    """
    install_rich_traceback(
        show_locals=show_locals,
        width=console.width,
        extra_lines=2,
        theme="monokai",
        word_wrap=True,
        suppress=[
            "typer",
            "click",
        ],  # Suppress framework internals for cleaner traces
    )
