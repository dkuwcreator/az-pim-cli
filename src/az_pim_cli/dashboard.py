"""Optional Textual-based dashboard for az-pim-cli.

This module provides a full-screen TUI (Text User Interface) dashboard
for viewing Azure PIM roles and activations in real-time.

Note: This module requires the 'tui' extra to be installed:
    pip install az-pim-cli[tui]

Reference:
- https://textual.textualize.io/
"""


def check_textual_available() -> bool:
    """Check if Textual is available."""
    try:
        import textual  # noqa: F401  # type: ignore[import-not-found]

        return True
    except ImportError:
        return False


def run_dashboard() -> None:
    """
    Run the dashboard TUI.

    Raises:
        ImportError: If textual is not installed
    """
    if not check_textual_available():
        from az_pim_cli import ui

        ui.error(
            "Textual Dashboard Not Available",
            detail="The dashboard feature requires the 'tui' extra.\n\n"
            "Install it with:\n"
            "  pip install az-pim-cli[tui]\n\n"
            "or:\n"
            "  pip install textual>=1.0.0",
        )
        raise ImportError("textual package not found")

    # Lazy import of Textual components
    from textual.app import App, ComposeResult
    from textual.containers import Container, VerticalScroll
    from textual.widgets import DataTable, Footer, Header, Static

    class PIMDashboard(App):
        """A Textual app for Azure PIM dashboard."""

        CSS = """
        Screen {
            background: $surface;
        }

        Header {
            background: $primary;
        }

        Footer {
            background: $primary;
        }

        DataTable {
            height: 1fr;
            margin: 1;
        }

        .info-panel {
            height: auto;
            margin: 1;
            padding: 1;
            background: $panel;
            border: solid $primary;
        }
        """

        BINDINGS = [
            ("q", "quit", "Quit"),
            ("r", "refresh", "Refresh"),
        ]

        def compose(self) -> ComposeResult:
            """Compose the dashboard layout."""
            yield Header()
            yield Container(
                Static(
                    "Azure PIM Dashboard\n\n"
                    "This is a preview of the TUI dashboard feature.\n"
                    "Press 'r' to refresh, 'q' to quit.",
                    classes="info-panel",
                ),
                VerticalScroll(
                    DataTable(id="roles-table"),
                ),
            )
            yield Footer()

        def on_mount(self) -> None:
            """Initialize the dashboard when mounted."""
            table = self.query_one("#roles-table", DataTable)
            table.add_columns("Role", "Status", "Scope", "Type")

            # Sample data - in real implementation, this would fetch from Azure
            table.add_row("Owner", "Eligible", "/subscriptions/...", "Azure RBAC")
            table.add_row("Contributor", "Active", "/subscriptions/...", "Azure RBAC")
            table.add_row("Global Administrator", "Eligible", "/", "Azure AD")
            table.add_row("Security Reader", "Eligible", "/", "Azure AD")

        def action_refresh(self) -> None:
            """Refresh the dashboard data."""
            # Placeholder for refresh logic
            self.notify("Dashboard refreshed (preview mode)")

    # Run the dashboard app
    app = PIMDashboard()
    app.run()
