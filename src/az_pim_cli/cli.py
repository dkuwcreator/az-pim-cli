"""Main CLI module for Azure PIM CLI."""

import os
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from az_pim_cli.auth import AzureAuth
from az_pim_cli.pim_client import PIMClient
from az_pim_cli.config import Config
from az_pim_cli.models import normalize_roles, RoleSource
from az_pim_cli.exceptions import (
    PIMError,
    NetworkError,
    PermissionError as PIMPermissionError,
    AuthenticationError,
)

app = typer.Typer(
    name="az-pim",
    help="Azure PIM CLI - Manage Azure Privileged Identity Management roles",
    no_args_is_help=True,
)

console = Console()


def parse_duration_from_alias(duration_str: Optional[str]) -> Optional[float]:
    """
    Parse duration from alias configuration.

    Args:
        duration_str: Duration string in PT format (e.g., PT8H)

    Returns:
        Duration in hours as float, or None
    """
    if not duration_str:
        return None
    # Remove PT prefix and H suffix, then convert to float
    return float(duration_str.replace("PT", "").replace("H", ""))


def get_duration_string(hours: Optional[float] = None) -> str:
    """
    Convert hours to ISO 8601 duration string.

    Args:
        hours: Duration in hours

    Returns:
        ISO 8601 duration string
    """
    if hours is None:
        return "PT8H"
    return f"PT{int(hours)}H"


@app.command("list")
def list_roles(
    resource: bool = typer.Option(
        False, "--resource", "-r", help="List resource roles instead of directory roles"
    ),
    scope: Optional[str] = typer.Option(
        None, "--scope", "-s", help="Scope for resource roles (e.g., subscriptions/{id})"
    ),
    full_scope: bool = typer.Option(
        False, "--full-scope", help="Show full scope paths instead of shortened versions"
    ),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of results"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    select: bool = typer.Option(
        False, "--select", help="Interactive mode: select and activate a role from the list"
    ),
) -> None:
    """List eligible roles."""
    try:
        auth = AzureAuth()
        client = PIMClient(auth, verbose=verbose)

        console.print("[bold blue]Fetching eligible roles...[/bold blue]")

        if resource:
            if not scope:
                # Default to current subscription
                subscription_id = auth.get_subscription_id()
                scope = f"subscriptions/{subscription_id}"

            roles_data = client.list_resource_role_assignments(scope, limit=limit)
            console.print(f"\n[bold green]Eligible Resource Roles (Scope: {scope})[/bold green]")
        else:
            roles_data = client.list_role_assignments(limit=limit)
            console.print("\n[bold green]Eligible Azure AD Roles[/bold green]")

        # Show backend info in verbose mode
        if verbose:
            backend = os.environ.get("AZ_PIM_BACKEND", "ARM")
            ipv4_mode = os.environ.get("AZ_PIM_IPV4_ONLY", "off")
            console.print(f"[dim]Backend: {backend} | IPv4-only: {ipv4_mode}[/dim]")

        # Normalize responses
        roles = normalize_roles(roles_data, source=RoleSource.ARM)

        if not roles:
            console.print("[yellow]No eligible roles found.[/yellow]")
            return

        console.print(f"[dim]Found {len(roles)} role(s)[/dim]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="bold white", justify="right")
        table.add_column("Role Name", style="cyan")
        table.add_column("Role ID", style="dim")
        table.add_column("Status", style="green")
        table.add_column("Scope", style="yellow")

        for idx, role in enumerate(roles, start=1):
            scope_display = role.scope if full_scope else role.get_short_scope()
            table.add_row(str(idx), role.name, role.id, role.status, scope_display)

        console.print(table)

        # Interactive selection mode
        if select:
            console.print()
            try:
                selection = typer.prompt(
                    "Enter role number to activate (or press Enter to cancel)", default=""
                )
                if not selection:
                    console.print("[yellow]Selection cancelled.[/yellow]")
                    return

                role_idx = int(selection) - 1
                if role_idx < 0 or role_idx >= len(roles):
                    console.print("[red]Invalid selection.[/red]")
                    raise typer.Exit(1)

                selected_role = roles[role_idx]
                console.print(
                    f"\n[bold blue]Selected:[/bold blue] {selected_role.name} ({selected_role.id})"
                )

                # Prompt for activation details
                duration_input = typer.prompt("Duration in hours", default="8")
                justification_input = typer.prompt(
                    "Justification", default="Requested via az-pim-cli"
                )

                duration = float(duration_input)
                duration_str = get_duration_string(duration)

                console.print(f"\n[bold blue]Activating role:[/bold blue] {selected_role.name}")
                console.print(f"[blue]Duration:[/blue] {duration_str}")
                console.print(f"[blue]Justification:[/blue] {justification_input}")

                if resource:
                    if not scope:
                        subscription_id = auth.get_subscription_id()
                        scope = f"subscriptions/{subscription_id}"
                    console.print(f"[blue]Scope:[/blue] {scope}\n")

                    result = client.request_resource_role_activation(
                        scope=scope,
                        role_definition_id=selected_role.id,
                        duration=duration_str,
                        justification=justification_input,
                    )
                else:
                    console.print()
                    result = client.request_role_activation(
                        role_definition_id=selected_role.id,
                        duration=duration_str,
                        justification=justification_input,
                    )

                console.print("[bold green]✓ Role activation requested successfully![/bold green]")
                console.print(f"[dim]Request ID: {result.get('id', 'N/A')}[/dim]")

            except ValueError:
                console.print("[red]Invalid input. Please enter a number.[/red]")
                raise typer.Exit(1)
            except (EOFError, KeyboardInterrupt):
                console.print("\n[yellow]Selection cancelled.[/yellow]")
                raise typer.Exit(0)

    except AuthenticationError as e:
        console.print(f"[bold red]Authentication Error:[/bold red] {str(e)}")
        if e.suggestion:
            console.print(f"[yellow]Suggestion:[/yellow] {e.suggestion}")
        raise typer.Exit(1)
    except NetworkError as e:
        console.print(f"[bold red]Network Error:[/bold red] {str(e)}")
        if e.endpoint:
            console.print(f"[dim]Endpoint: {e.endpoint}[/dim]")
        if e.suggest_ipv4:
            console.print(
                "[yellow]💡 Tip:[/yellow] If you're experiencing DNS issues, try enabling IPv4-only mode:"
            )
            console.print("   export AZ_PIM_IPV4_ONLY=1")
        raise typer.Exit(1)
    except PIMPermissionError as e:
        console.print(f"[bold red]Permission Error:[/bold red] {str(e)}")
        if e.endpoint:
            console.print(f"[dim]Endpoint: {e.endpoint}[/dim]")
        if e.required_permissions:
            console.print(f"[yellow]Required permissions:[/yellow] {e.required_permissions}")
        raise typer.Exit(1)
    except PIMError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected Error:[/bold red] {str(e)}")
        if verbose:
            import traceback

            console.print("[dim]" + traceback.format_exc() + "[/dim]")
        raise typer.Exit(1)


@app.command("activate")
def activate_role(
    role: str = typer.Argument(
        ..., help="Role name, ID, alias, or #N (number from list) to activate"
    ),
    duration: Optional[float] = typer.Option(None, "--duration", "-d", help="Duration in hours"),
    justification: Optional[str] = typer.Option(
        None, "--justification", "-j", help="Justification for activation"
    ),
    resource: bool = typer.Option(
        False, "--resource", "-r", help="Activate resource role instead of directory role"
    ),
    scope: Optional[str] = typer.Option(None, "--scope", "-s", help="Scope for resource roles"),
    ticket: Optional[str] = typer.Option(None, "--ticket", "-t", help="Ticket number"),
    ticket_system: Optional[str] = typer.Option(None, "--ticket-system", help="Ticket system name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Activate a role."""
    try:
        auth = AzureAuth()
        client = PIMClient(auth, verbose=verbose)
        config = Config()

        # Check if role is a number reference (e.g., "#1" or "1")
        if role.startswith("#") or role.isdigit():
            role_num = int(role.lstrip("#"))
            console.print(f"[blue]Looking up role #{role_num} from recent list...[/blue]")

            # Fetch roles
            if resource:
                if not scope:
                    subscription_id = auth.get_subscription_id()
                    scope = f"subscriptions/{subscription_id}"
                roles_data = client.list_resource_role_assignments(scope)
            else:
                roles_data = client.list_role_assignments()

            roles = normalize_roles(roles_data, source=RoleSource.ARM)

            if role_num < 1 or role_num > len(roles):
                console.print(
                    f"[red]Invalid role number. Please run 'az-pim list' to see available roles (1-{len(roles)}).[/red]"
                )
                raise typer.Exit(1)

            selected_role = roles[role_num - 1]
            role_id = selected_role.id
            console.print(f"[green]Selected:[/green] {selected_role.name}")
        # Check if role is an alias
        elif config.get_alias(role):
            alias = config.get_alias(role)
            console.print(f"[blue]Using alias '[bold]{role}[/bold]'[/blue]")
            role_id = alias.get("role")
            duration = duration or parse_duration_from_alias(alias.get("duration"))
            justification = justification or alias.get("justification")
            if "scope" in alias:
                scope = scope or alias.get("scope")
                if alias.get("scope") == "subscription":
                    resource = True
                    subscription = alias.get("subscription") or auth.get_subscription_id()
                    scope = f"subscriptions/{subscription}"
        else:
            role_id = role

        duration_str = get_duration_string(duration)
        justification = (
            justification or config.get_default("justification") or "Requested via az-pim-cli"
        )

        console.print(f"\n[bold blue]Activating role:[/bold blue] {role_id}")
        console.print(f"[blue]Duration:[/blue] {duration_str}")
        console.print(f"[blue]Justification:[/blue] {justification}")

        if resource:
            if not scope:
                subscription_id = auth.get_subscription_id()
                scope = f"subscriptions/{subscription_id}"
            console.print(f"[blue]Scope:[/blue] {scope}\n")

            result = client.request_resource_role_activation(
                scope=scope,
                role_definition_id=role_id,
                duration=duration_str,
                justification=justification,
                ticket_number=ticket,
                ticket_system=ticket_system,
            )
        else:
            console.print()
            result = client.request_role_activation(
                role_definition_id=role_id,
                duration=duration_str,
                justification=justification,
                ticket_number=ticket,
                ticket_system=ticket_system,
            )

        console.print("[bold green]✓ Role activation requested successfully![/bold green]")
        console.print(f"[dim]Request ID: {result.get('id', 'N/A')}[/dim]")

    except AuthenticationError as e:
        console.print(f"[bold red]Authentication Error:[/bold red] {str(e)}")
        if e.suggestion:
            console.print(f"[yellow]Suggestion:[/yellow] {e.suggestion}")
        raise typer.Exit(1)
    except NetworkError as e:
        console.print(f"[bold red]Network Error:[/bold red] {str(e)}")
        if e.endpoint:
            console.print(f"[dim]Endpoint: {e.endpoint}[/dim]")
        if e.suggest_ipv4:
            console.print("[yellow]💡 Tip:[/yellow] Try enabling IPv4-only mode:")
            console.print("   export AZ_PIM_IPV4_ONLY=1")
        raise typer.Exit(1)
    except PIMPermissionError as e:
        console.print(f"[bold red]Permission Error:[/bold red] {str(e)}")
        if e.endpoint:
            console.print(f"[dim]Endpoint: {e.endpoint}[/dim]")
        if e.required_permissions:
            console.print(f"[yellow]Required permissions:[/yellow] {e.required_permissions}")
        raise typer.Exit(1)
    except PIMError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected Error:[/bold red] {str(e)}")
        if verbose:
            import traceback

            console.print("[dim]" + traceback.format_exc() + "[/dim]")
        raise typer.Exit(1)


@app.command("history")
def view_history(
    days: int = typer.Option(30, "--days", "-d", help="Number of days to look back"),
    resource: bool = typer.Option(False, "--resource", "-r", help="Show resource role history"),
) -> None:
    """View activation history."""
    try:
        auth = AzureAuth()
        client = PIMClient(auth)

        console.print(f"[bold blue]Fetching activation history (last {days} days)...[/bold blue]")

        activations = client.list_activation_history(days=days)

        if not activations:
            console.print("[yellow]No activation history found.[/yellow]")
            return

        console.print("\n[bold green]Activation History[/bold green]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Role Name", style="cyan")
        table.add_column("Start Time", style="dim")
        table.add_column("End Time", style="dim")
        table.add_column("Status", style="green")

        for activation in activations:
            role_def = activation.get("roleDefinition", {})
            role_name = role_def.get("displayName", "Unknown")
            start_time = activation.get("startDateTime", "N/A")
            end_time = activation.get("endDateTime", "N/A")
            status = "Active"

            table.add_row(role_name, start_time, end_time, status)

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command("approve")
def approve_request(
    request_id: str = typer.Argument(..., help="Request ID to approve"),
    justification: Optional[str] = typer.Option(
        None, "--justification", "-j", help="Justification for approval"
    ),
) -> None:
    """Approve a pending role activation request."""
    try:
        auth = AzureAuth()
        client = PIMClient(auth)

        justification = justification or "Approved via az-pim-cli"

        console.print(f"\n[bold blue]Approving request:[/bold blue] {request_id}")
        console.print(f"[blue]Justification:[/blue] {justification}\n")

        client.approve_request(request_id, justification)

        console.print("[bold green]✓ Request approved successfully![/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command("pending")
def list_pending() -> None:
    """List pending approval requests."""
    try:
        auth = AzureAuth()
        client = PIMClient(auth)

        console.print("[bold blue]Fetching pending approval requests...[/bold blue]")

        requests = client.list_pending_approvals()

        if not requests:
            console.print("[yellow]No pending approval requests found.[/yellow]")
            return

        console.print("\n[bold green]Pending Approval Requests[/bold green]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Request ID", style="cyan")
        table.add_column("Principal", style="dim")
        table.add_column("Role", style="green")
        table.add_column("Created", style="dim")

        for req in requests:
            request_id = req.get("id", "N/A")
            principal_id = req.get("principalId", "N/A")
            role_id = req.get("roleDefinitionId", "N/A")
            created = req.get("createdDateTime", "N/A")

            table.add_row(request_id, principal_id, role_id, created)

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


# Alias management commands
alias_app = typer.Typer(help="Manage role aliases")
app.add_typer(alias_app, name="alias")


@alias_app.command("add")
def add_alias(
    name: str = typer.Argument(..., help="Alias name"),
    role: str = typer.Argument(..., help="Role name or ID"),
    duration: Optional[str] = typer.Option(None, "--duration", "-d", help="Duration (e.g., PT8H)"),
    justification: Optional[str] = typer.Option(
        None, "--justification", "-j", help="Justification"
    ),
    scope: Optional[str] = typer.Option(
        None, "--scope", "-s", help="Scope (directory, subscription)"
    ),
    subscription: Optional[str] = typer.Option(None, "--subscription", help="Subscription ID"),
) -> None:
    """Add a new alias."""
    try:
        config = Config()
        config.add_alias(
            name=name,
            role=role,
            duration=duration,
            justification=justification,
            scope=scope,
            subscription=subscription,
        )
        console.print(f"[bold green]✓ Alias '[bold]{name}[/bold]' added successfully![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


@alias_app.command("remove")
def remove_alias(name: str = typer.Argument(..., help="Alias name to remove")) -> None:
    """Remove an alias."""
    try:
        config = Config()
        if config.remove_alias(name):
            console.print(
                f"[bold green]✓ Alias '[bold]{name}[/bold]' removed successfully![/bold green]"
            )
        else:
            console.print(f"[yellow]Alias '[bold]{name}[/bold]' not found.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


@alias_app.command("list")
def list_aliases() -> None:
    """List all aliases."""
    try:
        config = Config()
        aliases = config.list_aliases()

        if not aliases:
            console.print("[yellow]No aliases configured.[/yellow]")
            return

        console.print("\n[bold green]Configured Aliases[/bold green]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Alias", style="cyan")
        table.add_column("Role", style="green")
        table.add_column("Duration", style="dim")
        table.add_column("Scope", style="dim")

        for alias_name, alias_config in aliases.items():
            role = alias_config.get("role", "N/A")
            duration = alias_config.get("duration", "Default")
            scope = alias_config.get("scope", "directory")

            table.add_row(alias_name, role, duration, scope)

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command("version")
def version() -> None:
    """Show version information."""
    from az_pim_cli import __version__

    console.print(
        f"[bold blue]az-pim-cli[/bold blue] version [bold green]{__version__}[/bold green]"
    )


if __name__ == "__main__":
    app()
