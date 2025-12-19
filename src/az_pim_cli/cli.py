"""Main CLI module for Azure PIM CLI - Split by PIM Subject."""

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

console = Console()

# Constants for scopes
ARM_SCOPE = "https://management.azure.com/.default"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"


def _log_verbose(scope: str, backend: str, command: str) -> None:
    """
    Log verbose information at the start of operations.

    Args:
        scope: The OAuth scope being used (ARM/Graph)
        backend: Backend hint (ARM/Graph)
        command: Command being executed
    """
    console.print(f"[dim]Command: {command}[/dim]")
    console.print(f"[dim]Scope: {scope}[/dim]")
    console.print(f"[dim]Backend: {backend}[/dim]")
    ipv4_mode = os.environ.get("AZ_PIM_IPV4_ONLY", "off")
    console.print(f"[dim]IPv4-only mode: {ipv4_mode}[/dim]")
    console.print()


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


# ============================================================================
# Azure Resources CLI (azp-res) - ARM-scoped
# ============================================================================

app_resources = typer.Typer(
    name="azp-res",
    help="Azure PIM for Resources - Manage Azure resource roles (ARM-scoped)",
    no_args_is_help=True,
)


@app_resources.command("list")
def list_resource_roles(
    scope: Optional[str] = typer.Option(
        None, "--scope", "-s", help="Scope for resource roles (e.g., subscriptions/{id})"
    ),
    full_scope: bool = typer.Option(
        False, "--full-scope", help="Show full scope paths instead of shortened versions"
    ),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of results"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """List eligible resource roles."""
    try:
        if verbose:
            _log_verbose(ARM_SCOPE, "ARM", "azp-res list")

        auth = AzureAuth()
        client = PIMClient(auth, verbose=verbose)

        if not scope:
            # Default to current subscription
            subscription_id = auth.get_subscription_id()
            scope = f"subscriptions/{subscription_id}"

        console.print("[bold blue]Fetching eligible resource roles...[/bold blue]")

        roles_data = client.list_resource_role_assignments(scope, limit=limit)
        azure_roles = normalize_roles(roles_data, source=RoleSource.ARM)

        console.print(f"\n[bold green]Eligible Resource Roles (Scope: {scope})[/bold green]")
        console.print(f"[dim]Found {len(azure_roles)} Azure role(s)[/dim]\n")

        if not azure_roles:
            console.print("[yellow]No eligible resource roles found.[/yellow]")
            console.print(
                "[yellow]💡 Tip:[/yellow] Ensure you have Reader + eligible PIM role assignments"
            )
            return

        # Display roles
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="bold white", justify="right", width=4)
        table.add_column("Role", style="cyan")
        table.add_column("Resource", style="yellow")
        table.add_column("Resource type", style="dim")
        table.add_column("Membership", style="dim")

        for idx, role in enumerate(azure_roles, start=1):
            resource_display = role.resource_name or (
                role.scope if full_scope else role.get_short_scope()
            )
            resource_type_display = role.resource_type or "-"
            membership_display = role.membership_type or "Eligible"

            table.add_row(
                str(idx),
                role.name,
                resource_display,
                resource_type_display,
                membership_display,
            )

        console.print(table)

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
                "[yellow]💡 Tip:[/yellow] If experiencing DNS issues, try: export AZ_PIM_IPV4_ONLY=1"
            )
        raise typer.Exit(1)
    except PIMPermissionError as e:
        console.print(f"[bold red]Permission Error:[/bold red] {str(e)}")
        console.print(
            "[yellow]💡 Tip:[/yellow] Ensure you have Reader + eligible PIM role assignments"
        )
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print("[dim]" + traceback.format_exc() + "[/dim]")
        raise typer.Exit(1)


@app_resources.command("activate")
def activate_resource_role(
    role: str = typer.Argument(..., help="Role ID to activate"),
    duration: Optional[float] = typer.Option(None, "--duration", "-d", help="Duration in hours"),
    justification: Optional[str] = typer.Option(
        None, "--justification", "-j", help="Justification for activation"
    ),
    scope: Optional[str] = typer.Option(
        None, "--scope", "-s", help="Scope for resource roles (e.g., subscriptions/{id})"
    ),
    ticket: Optional[str] = typer.Option(None, "--ticket", "-t", help="Ticket number"),
    ticket_system: Optional[str] = typer.Option(None, "--ticket-system", help="Ticket system name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Activate a resource role."""
    try:
        if verbose:
            _log_verbose(ARM_SCOPE, "ARM", "azp-res activate")

        auth = AzureAuth()
        client = PIMClient(auth, verbose=verbose)

        if not scope:
            subscription_id = auth.get_subscription_id()
            scope = f"subscriptions/{subscription_id}"

        duration_str = get_duration_string(duration)
        justification = justification or "Requested via azp-res"

        console.print(f"\n[bold blue]Activating resource role:[/bold blue] {role}")
        console.print(f"[blue]Duration:[/blue] {duration_str}")
        console.print(f"[blue]Justification:[/blue] {justification}")
        console.print(f"[blue]Scope:[/blue] {scope}\n")

        result = client.request_resource_role_activation(
            scope=scope,
            role_definition_id=role,
            duration=duration_str,
            justification=justification,
            ticket_number=ticket,
            ticket_system=ticket_system,
        )

        console.print("[bold green]✓ Resource role activation requested successfully![/bold green]")
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
            console.print("[yellow]💡 Tip:[/yellow] Try: export AZ_PIM_IPV4_ONLY=1")
        raise typer.Exit(1)
    except PIMPermissionError as e:
        console.print(f"[bold red]Permission Error:[/bold red] {str(e)}")
        console.print(
            "[yellow]💡 Tip:[/yellow] Ensure you have Reader + eligible PIM role assignments"
        )
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print("[dim]" + traceback.format_exc() + "[/dim]")
        raise typer.Exit(1)


@app_resources.command("version")
def version_resources() -> None:
    """Show version information."""
    from az_pim_cli import __version__

    console.print(
        f"[bold blue]azp-res[/bold blue] version [bold green]{__version__}[/bold green]"
    )


# ============================================================================
# Entra Roles CLI (azp-entra) - Graph-scoped
# ============================================================================

app_entra = typer.Typer(
    name="azp-entra",
    help="Azure PIM for Entra Roles - Manage Entra ID directory roles (Graph-scoped)",
    no_args_is_help=True,
)


@app_entra.command("list")
def list_entra_roles(
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of results"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """List eligible Entra directory roles."""
    try:
        if verbose:
            _log_verbose(GRAPH_SCOPE, "Graph", "azp-entra list")

        auth = AzureAuth()
        client = PIMClient(auth, verbose=verbose)

        console.print("[bold blue]Fetching eligible Entra roles...[/bold blue]")

        roles_data = client.list_role_assignments(limit=limit)
        azure_roles = normalize_roles(roles_data, source=RoleSource.ARM)

        console.print("\n[bold green]Eligible Entra Directory Roles[/bold green]")
        console.print(f"[dim]Found {len(azure_roles)} Azure role(s)[/dim]\n")

        if not azure_roles:
            console.print("[yellow]No eligible Entra roles found.[/yellow]")
            console.print(
                "[yellow]💡 Tip:[/yellow] Ensure you have Graph permissions (PrivilegedAccess.Read.AzureAD)"
            )
            return

        # Display roles
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="bold white", justify="right", width=4)
        table.add_column("Role", style="cyan")
        table.add_column("Scope", style="yellow")
        table.add_column("Status", style="green")

        for idx, role in enumerate(azure_roles, start=1):
            scope_display = role.scope or "/"
            status_display = role.status or "Eligible"

            table.add_row(str(idx), role.name, scope_display, status_display)

        console.print(table)

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
            console.print("[yellow]💡 Tip:[/yellow] Try: export AZ_PIM_IPV4_ONLY=1")
        raise typer.Exit(1)
    except PIMPermissionError as e:
        console.print(f"[bold red]Permission Error:[/bold red] {str(e)}")
        console.print(
            "[yellow]💡 Tip:[/yellow] Ensure Graph permissions (PrivilegedAccess.Read.AzureAD)"
        )
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print("[dim]" + traceback.format_exc() + "[/dim]")
        raise typer.Exit(1)


@app_entra.command("activate")
def activate_entra_role(
    role: str = typer.Argument(..., help="Role ID to activate"),
    duration: Optional[float] = typer.Option(None, "--duration", "-d", help="Duration in hours"),
    justification: Optional[str] = typer.Option(
        None, "--justification", "-j", help="Justification for activation"
    ),
    ticket: Optional[str] = typer.Option(None, "--ticket", "-t", help="Ticket number"),
    ticket_system: Optional[str] = typer.Option(None, "--ticket-system", help="Ticket system name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Activate an Entra directory role."""
    try:
        if verbose:
            _log_verbose(GRAPH_SCOPE, "Graph", "azp-entra activate")

        auth = AzureAuth()
        client = PIMClient(auth, verbose=verbose)

        duration_str = get_duration_string(duration)
        justification = justification or "Requested via azp-entra"

        console.print(f"\n[bold blue]Activating Entra role:[/bold blue] {role}")
        console.print(f"[blue]Duration:[/blue] {duration_str}")
        console.print(f"[blue]Justification:[/blue] {justification}\n")

        result = client.request_role_activation(
            role_definition_id=role,
            duration=duration_str,
            justification=justification,
            ticket_number=ticket,
            ticket_system=ticket_system,
        )

        console.print("[bold green]✓ Entra role activation requested successfully![/bold green]")
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
            console.print("[yellow]💡 Tip:[/yellow] Try: export AZ_PIM_IPV4_ONLY=1")
        raise typer.Exit(1)
    except PIMPermissionError as e:
        console.print(f"[bold red]Permission Error:[/bold red] {str(e)}")
        console.print(
            "[yellow]💡 Tip:[/yellow] Ensure Graph permissions (PrivilegedAccess.Read.AzureAD)"
        )
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print("[dim]" + traceback.format_exc() + "[/dim]")
        raise typer.Exit(1)


@app_entra.command("history")
def view_entra_history(
    days: int = typer.Option(30, "--days", "-d", help="Number of days to look back"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """View Entra role activation history."""
    try:
        if verbose:
            _log_verbose(GRAPH_SCOPE, "Graph", "azp-entra history")

        auth = AzureAuth()
        client = PIMClient(auth, verbose=verbose)

        console.print(f"[bold blue]Fetching Entra role activation history (last {days} days)...[/bold blue]")

        activations = client.list_activation_history(days=days)

        if not activations:
            console.print("[yellow]No activation history found.[/yellow]")
            return

        console.print("\n[bold green]Entra Role Activation History[/bold green]\n")

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
        if verbose:
            import traceback
            console.print("[dim]" + traceback.format_exc() + "[/dim]")
        raise typer.Exit(1)


@app_entra.command("approve")
def approve_entra_request(
    request_id: str = typer.Argument(..., help="Request ID to approve"),
    justification: Optional[str] = typer.Option(
        None, "--justification", "-j", help="Justification for approval"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Approve a pending Entra role activation request."""
    try:
        if verbose:
            _log_verbose(GRAPH_SCOPE, "Graph", "azp-entra approve")

        auth = AzureAuth()
        client = PIMClient(auth, verbose=verbose)

        justification = justification or "Approved via azp-entra"

        console.print(f"\n[bold blue]Approving Entra role request:[/bold blue] {request_id}")
        console.print(f"[blue]Justification:[/blue] {justification}\n")

        client.approve_request(request_id, justification)

        console.print("[bold green]✓ Entra role request approved successfully![/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print("[dim]" + traceback.format_exc() + "[/dim]")
        raise typer.Exit(1)


@app_entra.command("pending")
def list_entra_pending(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """List pending Entra role approval requests."""
    try:
        if verbose:
            _log_verbose(GRAPH_SCOPE, "Graph", "azp-entra pending")

        auth = AzureAuth()
        client = PIMClient(auth, verbose=verbose)

        console.print("[bold blue]Fetching pending Entra role approval requests...[/bold blue]")

        requests = client.list_pending_approvals()

        if not requests:
            console.print("[yellow]No pending approval requests found.[/yellow]")
            return

        console.print("\n[bold green]Pending Entra Role Approval Requests[/bold green]\n")

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
        if verbose:
            import traceback
            console.print("[dim]" + traceback.format_exc() + "[/dim]")
        raise typer.Exit(1)


@app_entra.command("version")
def version_entra() -> None:
    """Show version information."""
    from az_pim_cli import __version__

    console.print(
        f"[bold blue]azp-entra[/bold blue] version [bold green]{__version__}[/bold green]"
    )


# ============================================================================
# Entra Groups CLI (azp-groups) - Graph-scoped
# ============================================================================

app_groups = typer.Typer(
    name="azp-groups",
    help="Azure PIM for Groups - Manage Entra group memberships (Graph-scoped)",
    no_args_is_help=True,
)


@app_groups.command("list")
def list_group_roles(
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of results"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """List eligible group assignments."""
    try:
        if verbose:
            _log_verbose(GRAPH_SCOPE, "Graph", "azp-groups list")

        auth = AzureAuth()
        client = PIMClient(auth, verbose=verbose)

        console.print("[bold blue]Fetching eligible group assignments...[/bold blue]")

        groups_data = client.list_group_assignments(limit=limit)

        console.print("\n[bold green]Eligible Group Assignments[/bold green]")
        console.print(f"[dim]Found {len(groups_data)} group assignment(s)[/dim]\n")

        if not groups_data:
            console.print("[yellow]No eligible group assignments found.[/yellow]")
            console.print(
                "[yellow]💡 Tip:[/yellow] Ensure Graph permissions (PrivilegedAccess.Read.AzureADGroup)"
            )
            return

        # Display groups
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="bold white", justify="right", width=4)
        table.add_column("Group", style="cyan")
        table.add_column("Access", style="yellow")
        table.add_column("Status", style="green")

        for idx, group in enumerate(groups_data, start=1):
            group_info = group.get("group", {})
            group_name = group_info.get("displayName", "Unknown")
            access_id = group.get("accessId", "member")
            status = group.get("status", "Eligible")

            table.add_row(str(idx), group_name, access_id, status)

        console.print(table)

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
            console.print("[yellow]💡 Tip:[/yellow] Try: export AZ_PIM_IPV4_ONLY=1")
        raise typer.Exit(1)
    except PIMPermissionError as e:
        console.print(f"[bold red]Permission Error:[/bold red] {str(e)}")
        console.print(
            "[yellow]💡 Tip:[/yellow] Ensure Graph permissions (PrivilegedAccess.Read.AzureADGroup)"
        )
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print("[dim]" + traceback.format_exc() + "[/dim]")
        raise typer.Exit(1)


@app_groups.command("activate")
def activate_group_role(
    group_id: str = typer.Argument(..., help="Group ID to activate"),
    access: str = typer.Option("member", "--access", "-a", help="Access type (member or owner)"),
    duration: Optional[float] = typer.Option(None, "--duration", "-d", help="Duration in hours"),
    justification: Optional[str] = typer.Option(
        None, "--justification", "-j", help="Justification for activation"
    ),
    ticket: Optional[str] = typer.Option(None, "--ticket", "-t", help="Ticket number"),
    ticket_system: Optional[str] = typer.Option(None, "--ticket-system", help="Ticket system name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Activate a group assignment."""
    try:
        if verbose:
            _log_verbose(GRAPH_SCOPE, "Graph", "azp-groups activate")

        auth = AzureAuth()
        client = PIMClient(auth, verbose=verbose)

        duration_str = get_duration_string(duration)
        justification = justification or "Requested via azp-groups"

        console.print(f"\n[bold blue]Activating group assignment:[/bold blue] {group_id}")
        console.print(f"[blue]Access:[/blue] {access}")
        console.print(f"[blue]Duration:[/blue] {duration_str}")
        console.print(f"[blue]Justification:[/blue] {justification}\n")

        result = client.activate_group_role(
            group_id=group_id,
            access_id=access,
            duration=duration_str,
            justification=justification,
            ticket_number=ticket,
            ticket_system=ticket_system,
        )

        console.print("[bold green]✓ Group assignment activation requested successfully![/bold green]")
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
            console.print("[yellow]💡 Tip:[/yellow] Try: export AZ_PIM_IPV4_ONLY=1")
        raise typer.Exit(1)
    except PIMPermissionError as e:
        console.print(f"[bold red]Permission Error:[/bold red] {str(e)}")
        console.print(
            "[yellow]💡 Tip:[/yellow] Ensure Graph permissions (PrivilegedAccess.ReadWrite.AzureADGroup)"
        )
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print("[dim]" + traceback.format_exc() + "[/dim]")
        raise typer.Exit(1)


@app_groups.command("version")
def version_groups() -> None:
    """Show version information."""
    from az_pim_cli import __version__

    console.print(
        f"[bold blue]azp-groups[/bold blue] version [bold green]{__version__}[/bold green]"
    )
