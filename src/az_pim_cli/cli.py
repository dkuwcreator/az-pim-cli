"""Main CLI module for Azure PIM CLI."""

import os
from typing import Optional

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from az_pim_cli.auth import AzureAuth
from az_pim_cli.config import Config
from az_pim_cli.models import normalize_roles, RoleSource, SUBSCRIPTION_ID_DISPLAY_LENGTH
from az_pim_cli.exceptions import (
    AuthenticationError,
    NetworkError,
)
from az_pim_cli.exceptions import PermissionError as PIMPermissionError
from az_pim_cli.exceptions import (
    PIMError,
)
from az_pim_cli.models import RoleSource, normalize_roles
from az_pim_cli.pim_client import PIMClient

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
        from az_pim_cli.models import alias_to_normalized_role

        auth = AzureAuth()
        client = PIMClient(auth, verbose=verbose)
        config = Config()

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

        # Normalize responses from Azure
        azure_roles = normalize_roles(roles_data, source=RoleSource.ARM)

        # Load aliases and convert to NormalizedRole objects
        aliases = config.list_aliases()
        alias_roles = []
        alias_configs = []  # Store configs to avoid redundant lookups
        for alias_name, alias_config in aliases.items():
            alias_role = alias_to_normalized_role(alias_name, alias_config)
            alias_roles.append(alias_role)
            alias_configs.append(alias_config)

        # Combine aliases first, then Azure roles (for numbering consistency)
        all_roles = alias_roles + azure_roles

        if not all_roles:
            console.print("[yellow]No eligible roles or aliases found.[/yellow]")
            return

        console.print(
            f"[dim]Found {len(alias_roles)} alias(es) and {len(azure_roles)} Azure role(s)[/dim]\n"
        )

        # Display aliases in a separate table first
        if alias_roles:
            console.print("[bold green]Configured Aliases[/bold green]")
            alias_table = Table(show_header=True, header_style="bold magenta")
            alias_table.add_column("#", style="bold white", justify="right", width=4)
            alias_table.add_column("Alias", style="cyan")
            alias_table.add_column("Role", style="yellow")
            alias_table.add_column("Duration", style="green")
            alias_table.add_column("Description", style="dim")
            alias_table.add_column("Scope", style="dim")

            for idx, (alias_role, alias_config) in enumerate(zip(alias_roles, alias_configs), start=1):
                # Extract alias details
                alias_name = alias_role.alias_name or "Unknown"
                role_name = alias_role.name
                duration_display = alias_role.end_time if alias_role.end_time else "-"
                
                # Get description from the already-fetched alias config
                description = alias_config.get("justification", "-") if alias_config else "-"
                
                # Format scope display
                scope_display = alias_role.resource_name or (
                    alias_role.scope if full_scope else alias_role.get_short_scope()
                )

                alias_table.add_row(
                    str(idx),
                    alias_name,
                    role_name,
                    duration_display,
                    description,
                    scope_display,
                )

            console.print(alias_table)
            console.print()

        # Display Azure roles in a separate table
        if azure_roles:
            role_type = "Resource Roles" if resource else "Azure AD Roles"
            console.print(f"[bold green]Eligible {role_type}[/bold green]")
            
            roles_table = Table(show_header=True, header_style="bold magenta")
            roles_table.add_column("#", style="bold white", justify="right", width=4)
            roles_table.add_column("Role", style="cyan")
            roles_table.add_column("Resource", style="yellow")
            roles_table.add_column("Resource type", style="dim")
            roles_table.add_column("Membership", style="dim")
            roles_table.add_column("Condition", style="dim")
            roles_table.add_column("End time", style="green")

            for idx, role in enumerate(azure_roles, start=len(alias_roles) + 1):
                # Get resource info
                resource_display = role.resource_name or (
                    role.scope if full_scope else role.get_short_scope()
                )
                resource_type_display = role.resource_type or "-"
                membership_display = role.membership_type or "Eligible"
                condition_display = role.condition if role.condition else "-"
                end_time_display = role.end_time if role.end_time else "-"

                roles_table.add_row(
                    str(idx),
                    role.name,
                    resource_display,
                    resource_type_display,
                    membership_display,
                    condition_display,
                    end_time_display,
                )

            console.print(roles_table)

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
                if role_idx < 0 or role_idx >= len(all_roles):
                    console.print("[red]Invalid selection.[/red]")
                    raise typer.Exit(1)

                selected_role = all_roles[role_idx]
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
        from az_pim_cli.models import alias_to_normalized_role

        auth = AzureAuth()
        client = PIMClient(auth, verbose=verbose)
        config = Config()

        role_id = None

        # Check if role is a number reference (e.g., "#1" or "1")
        if role.startswith("#") or role.isdigit():
            try:
                role_num = int(role.lstrip("#"))
            except ValueError:
                console.print(
                    f"[red]Invalid role number format: '{role}'. Expected a number like '1' or '#1'.[/red]"
                )
                raise typer.Exit(1)

            console.print(f"[blue]Looking up role #{role_num} from recent list...[/blue]")

            # Load aliases first
            aliases = config.list_aliases()
            alias_roles = []
            for alias_name, alias_config in aliases.items():
                alias_role = alias_to_normalized_role(alias_name, alias_config)
                alias_roles.append(alias_role)

            # Fetch roles - note: this fetches all roles to ensure consistent ordering
            # with the list command. For better performance, run 'az-pim list' first
            # to see available roles, then activate by number.
            if resource:
                if not scope:
                    subscription_id = auth.get_subscription_id()
                    scope = f"subscriptions/{subscription_id}"
                roles_data = client.list_resource_role_assignments(scope)
            else:
                roles_data = client.list_role_assignments()

            azure_roles = normalize_roles(roles_data, source=RoleSource.ARM)

            # Combine alias roles and Azure roles (same order as list command)
            all_roles = alias_roles + azure_roles

            if role_num < 1 or role_num > len(all_roles):
                console.print(
                    f"[red]Invalid role number. Please run 'az-pim list' to see available roles (1-{len(all_roles)}).[/red]"
                )
                raise typer.Exit(1)

            selected_role = all_roles[role_num - 1]

            # If the selected role is an alias, use the alias activation path
            if selected_role.is_alias:
                role = selected_role.alias_name or role
            else:
                role_id = selected_role.id
                console.print(f"[green]Selected:[/green] {selected_role.name}")

        # Check if role is an alias
        if not role_id and config.get_alias(role):
            alias = config.get_alias(role)
            console.print(f"[blue]Using alias '[bold]{role}[/bold]'[/blue]")

            # Get role from alias, prompt if missing
            role_id = alias.get("role")
            if not role_id:
                console.print("[yellow]Alias is missing 'role' field.[/yellow]")
                role_id = typer.prompt("Enter role name or ID")

            # Merge alias defaults with command-line overrides
            duration = duration or parse_duration_from_alias(alias.get("duration"))
            justification = justification or alias.get("justification")

            # Handle scope from alias
            if "scope" in alias:
                alias_scope = alias.get("scope")
                if alias_scope == "subscription":
                    resource = True
                    subscription = alias.get("subscription")
                    if not subscription:
                        # Prompt for subscription if missing
                        subscription = typer.prompt(
                            "Enter subscription ID", default=auth.get_subscription_id()
                        )
                    scope = scope or f"subscriptions/{subscription}"
                    if alias.get("resource_group"):
                        scope = scope or f"{scope}/resourceGroups/{alias['resource_group']}"
                elif alias_scope == "directory":
                    scope = scope or "/"

            # Prompt for scope if still missing and resource flag is set
            if resource and not scope:
                console.print(
                    "[yellow]Resource scope is required for resource role activation.[/yellow]"
                )
                default_sub = auth.get_subscription_id()
                scope = typer.prompt("Enter scope", default=f"subscriptions/{default_sub}")
        elif not role_id:
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
    role: Optional[str] = typer.Argument(None, help="Role name or ID"),
    duration: Optional[str] = typer.Option(None, "--duration", "-d", help="Duration (e.g., PT8H)"),
    justification: Optional[str] = typer.Option(
        None, "--justification", "-j", help="Justification"
    ),
    scope: Optional[str] = typer.Option(
        None, "--scope", "-s", help="Scope (directory, subscription)"
    ),
    subscription: Optional[str] = typer.Option(None, "--subscription", help="Subscription ID"),
    resource: Optional[str] = typer.Option(None, "--resource", help="Resource name"),
    resource_type: Optional[str] = typer.Option(None, "--resource-type", help="Resource type"),
    membership: Optional[str] = typer.Option(None, "--membership", help="Membership type"),
    condition: Optional[str] = typer.Option(None, "--condition", help="Condition expression"),
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
            resource=resource,
            resource_type=resource_type,
            membership=membership,
            condition=condition,
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
    """List all aliases with their details."""
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
        table.add_column("Duration", style="yellow")
        table.add_column("Description", style="dim")
        table.add_column("Scope", style="dim")

        for alias_name, alias_config in aliases.items():
            role = alias_config.get("role", "N/A")
            duration = alias_config.get("duration", "Default")
            description = alias_config.get("justification", "-")
            scope = alias_config.get("scope", "directory")
            
            # Add subscription info to scope if present
            subscription_id = alias_config.get("subscription", "")
            if scope == "subscription" and subscription_id:
                sub_id = subscription_id[:SUBSCRIPTION_ID_DISPLAY_LENGTH]
                scope = f"{scope} (sub:{sub_id}...)"

            table.add_row(alias_name, role, duration, description, scope)

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


@alias_app.command("view")
def view_config() -> None:
    """Open the config file in the system editor."""
    import platform
    import subprocess

    try:
        config = Config()
        config_path = config.get_config_path()

        # Ensure config file exists
        if not config_path.exists():
            config.save()

        # Get editor from environment or use platform defaults
        editor = os.environ.get("EDITOR")

        if not editor:
            system = platform.system()
            if system == "Windows":
                editor = "notepad"
            elif system == "Darwin":  # macOS
                editor = "open"
            else:  # Linux and others
                editor = "nano"

        console.print(f"[blue]Opening config file in {editor}...[/blue]")
        console.print(f"[dim]Config path: {config_path}[/dim]\n")

        subprocess.run([editor, str(config_path)], check=True)

        console.print("[green]✓ Config file closed.[/green]")

    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error:[/bold red] Failed to open editor: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


@alias_app.command("edit")
def edit_alias(name: str = typer.Argument(..., help="Alias name to edit")) -> None:
    """Edit an alias interactively."""
    try:
        config = Config()
        alias = config.get_alias(name)

        if not alias:
            console.print(f"[yellow]Alias '[bold]{name}[/bold]' not found.[/yellow]")
            create_new = typer.confirm("Would you like to create it?")
            if not create_new:
                raise typer.Exit(0)
            alias = {}

        console.print(f"\n[bold blue]Editing alias '[bold]{name}[/bold]'[/bold blue]")
        console.print("[dim]Press Enter to keep current value, or enter new value[/dim]\n")

        # Edit each field interactively
        current_role = alias.get("role", "")
        role = (
            typer.prompt("Role name or ID", default=current_role)
            if current_role
            else typer.prompt("Role name or ID", default="")
        )

        current_duration = alias.get("duration", "")
        duration = (
            typer.prompt("Duration (e.g., PT8H)", default=current_duration)
            if current_duration
            else typer.prompt("Duration (e.g., PT8H)", default="")
        )

        current_justification = alias.get("justification", "")
        justification = (
            typer.prompt("Justification", default=current_justification)
            if current_justification
            else typer.prompt("Justification", default="")
        )

        current_scope = alias.get("scope", "")
        scope = (
            typer.prompt("Scope (directory/subscription/resource)", default=current_scope)
            if current_scope
            else typer.prompt("Scope (directory/subscription/resource)", default="")
        )

        current_subscription = alias.get("subscription", "")
        subscription = (
            typer.prompt("Subscription ID (optional)", default=current_subscription)
            if current_subscription
            else typer.prompt("Subscription ID (optional)", default="")
        )

        current_resource = alias.get("resource", "")
        resource = (
            typer.prompt("Resource name (optional)", default=current_resource)
            if current_resource
            else typer.prompt("Resource name (optional)", default="")
        )

        current_resource_type = alias.get("resource_type", "")
        resource_type = (
            typer.prompt("Resource type (optional)", default=current_resource_type)
            if current_resource_type
            else typer.prompt("Resource type (optional)", default="")
        )

        current_membership = alias.get("membership", "")
        membership = (
            typer.prompt("Membership type (optional)", default=current_membership)
            if current_membership
            else typer.prompt("Membership type (optional)", default="")
        )

        current_condition = alias.get("condition", "")
        condition = (
            typer.prompt("Condition (optional)", default=current_condition)
            if current_condition
            else typer.prompt("Condition (optional)", default="")
        )

        # Save the alias
        config.add_alias(
            name=name,
            role=role or None,
            duration=duration or None,
            justification=justification or None,
            scope=scope or None,
            subscription=subscription or None,
            resource=resource or None,
            resource_type=resource_type or None,
            membership=membership or None,
            condition=condition or None,
        )

        console.print(
            f"\n[bold green]✓ Alias '[bold]{name}[/bold]' saved successfully![/bold green]"
        )

    except (EOFError, KeyboardInterrupt):
        console.print("\n[yellow]Edit cancelled.[/yellow]")
        raise typer.Exit(0)
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
