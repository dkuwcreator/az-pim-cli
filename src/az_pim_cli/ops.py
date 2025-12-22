"""Progress and status operations for az-pim-cli.

This module provides helpers for showing progress bars and status spinners
during long-running operations.

Reference:
- https://rich.readthedocs.io/en/stable/progress.html
- https://rich.readthedocs.io/en/stable/console.html#status
"""

from collections.abc import Generator
from contextlib import contextmanager

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from az_pim_cli.console import console


@contextmanager
def status(message: str, spinner: str = "dots") -> Generator[None, None, None]:
    """
    Context manager for showing a status spinner during short tasks.

    Args:
        message: Status message to display
        spinner: Spinner type (default: "dots")

    Example:
        with status("Fetching roles..."):
            roles = client.list_roles()
    """
    with console.status(f"[bold blue]{message}[/bold blue]", spinner=spinner):
        yield


@contextmanager
def progress_bar(
    *,
    transient: bool = True,
    description: str | None = None,
) -> Generator[Progress, None, None]:
    """
    Context manager for showing a progress bar during multi-step operations.

    Args:
        transient: If True, progress bar disappears after completion (default: True)
        description: Optional description for the progress bar

    Example:
        with progress_bar(description="Processing roles") as progress:
            task = progress.add_task("Processing...", total=len(roles))
            for role in roles:
                # ... do work ...
                progress.advance(task)
    """
    prog = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=transient,
    )

    with prog:
        yield prog


def show_progress(
    items: list, description: str = "Processing", transient: bool = True
) -> Generator:
    """
    Simple progress bar for iterating over items.

    Args:
        items: List of items to process
        description: Description of the operation
        transient: If True, progress bar disappears after completion

    Yields:
        Each item from the input list

    Example:
        for role in show_progress(roles, "Activating roles"):
            activate_role(role)
    """
    with progress_bar(transient=transient) as progress:
        task = progress.add_task(f"[cyan]{description}...", total=len(items))
        for item in items:
            yield item
            progress.advance(task)
