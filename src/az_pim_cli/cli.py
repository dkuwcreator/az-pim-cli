"""Main CLI module for Azure PIM CLI."""

import os
import sys
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from az_pim_cli.auth import AzureAuth, should_use_ipv4_only
from az_pim_cli.config import Config
from az_pim_cli.domain.models import NormalizedRole
from az_pim_cli.exceptions import (
    AuthenticationError,
    NetworkError,
    PIMError,
)
from az_pim_cli.exceptions import PermissionError as PIMPermissionError
from az_pim_cli.models import (
    SUBSCRIPTION_ID_DISPLAY_LENGTH,
    RoleSource,
    normalize_roles,
)
from az_pim_cli.pim_client import PIMClient
from az_pim_cli.resolver import InputResolver, resolve_role

# Default backend for PIM operations
DEFAULT_BACKEND = "ARM"

app = typer.Typer(
    name="az-pim",
    help="Azure PIM CLI - Manage Azure Privileged Identity Management roles",
    no_args_is_help=True,
)

console = Console()


def get_resolver(config: Config, is_tty: bool | None = None) -> InputResolver:
    """
    Get a configured InputResolver instance.

    Args:
        config: Config instance
        is_tty: Whether running in a TTY

    Returns:
        InputResolver configured from settings
    """
    fuzzy_enabled_value = config.get_default("fuzzy_matching", True)
    fuzzy_enabled = bool(fuzzy_enabled_value) if fuzzy_enabled_value is not None else True

    fuzzy_threshold_value = config.get_default("fuzzy_threshold", 0.8)
    fuzzy_threshold = float(fuzzy_threshold_value) if fuzzy_threshold_value is not None else 0.8

    cache_ttl_value = config.get_default("cache_ttl_seconds", 300)
    cache_ttl = int(cache_ttl_value) if cache_ttl_value is not None else 300

    return InputResolver(
        fuzzy_enabled=fuzzy_enabled,
        fuzzy_threshold=fuzzy_threshold,
        cache_ttl_seconds=cache_ttl,
        is_tty=is_tty,
    )


def resolve_scope_input(
    scope_input: str, auth: AzureAuth, client: Any | None = None, config: Config | None = None
) -> str:
    """
    Resolve user-provided scope input to a full Azure scope path.
    Supports subscriptions, management groups, and resource groups.

    Args:
        scope_input: User-provided scope (name, partial path, etc.)
        auth: AzureAuth instance for getting subscription context
        client: Optional PIMClient for fetching available scopes
        config: Optional Config for resolver settings

    Returns:
        Full scope path
    """
    # If already a full path, return as-is (ensure leading slash)
    if scope_input.startswith("/subscriptions/") or scope_input.startswith("/providers/"):
        return scope_input

    if scope_input.startswith("subscriptions/"):
        return f"/{scope_input}"

    # If it contains "subscriptions/" somewhere, try to extract and normalize
    if "subscriptions/" in scope_input:
        # Ensure leading slash
        return f"/{scope_input}" if not scope_input.startswith("/") else scope_input

    # Try to resolve against available scopes if client provided
    if client and config:
        try:
            resolver = get_resolver(config)
            subscription_id = auth.get_subscription_id()

            def fetch_scopes() -> list[dict[str, str]]:
                """Fetch available scopes: management groups, subscriptions, and resource groups."""
                scopes: list[dict[str, str]] = []

                # Add current subscription
                scopes.append(
                    {
                        "id": f"/subscriptions/{subscription_id}",
                        "name": subscription_id,
                        "type": "subscription",
                    }
                )

                # Fetch eligible resource role assignments to discover scopes
                try:
                    roles_data = client.list_resource_role_assignments(
                        f"subscriptions/{subscription_id}"
                    )
                    # Extract unique scopes from roles
                    seen_scopes = set()
                    for role in roles_data:
                        scope_id = (
                            role.get("properties", {})
                            .get("expandedProperties", {})
                            .get("scope", {})
                            .get("id")
                        )
                        if not scope_id:
                            continue
                        if scope_id in seen_scopes:
                            continue
                        seen_scopes.add(scope_id)

                        # Extract name from scope
                        scope_name = scope_id.split("/")[-1] if "/" in scope_id else scope_id

                        # Determine type
                        scope_type = "unknown"
                        if "/managementGroups/" in scope_id:
                            scope_type = "managementGroup"
                        elif "/resourceGroups/" in scope_id:
                            scope_type = "resourceGroup"
                        elif "/subscriptions/" in scope_id and scope_id.count("/") == 2:
                            scope_type = "subscription"

                        scopes.append({"id": scope_id, "name": scope_name, "type": scope_type})
                except Exception:
                    # If we can't fetch scopes, fall back to basic resolution
                    pass

                return scopes

            def extract_scope_id(scope: dict[str, Any]) -> str:
                name = scope.get("name", "")
                return str(name) if name else ""

            resolved = resolver.resolve(
                user_input=scope_input,
                candidates=fetch_scopes(),
                name_extractor=extract_scope_id,
                context="scope",
                allow_interactive=True,
            )

            if resolved and isinstance(resolved, dict):
                scope_id = resolved.get("id", "")
                if isinstance(scope_id, str) and scope_id:
                    return scope_id
        except Exception:
            # Fall through to default behavior
            pass

    # Default: treat as resource group name within current subscription
    subscription_id = auth.get_subscription_id()
    return f"/subscriptions/{subscription_id}/resourceGroups/{scope_input}"


def parse_duration_from_alias(duration_str: str | None) -> float | None:
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


def get_duration_string(hours: float | None = None) -> str:
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
    scope: str | None = typer.Option(
        None, "--scope", "-s", help="Scope for resource roles (e.g., subscriptions/{id})"
    ),
    full_scope: bool = typer.Option(
        False, "--full-scope", help="Show full scope paths instead of shortened versions"
    ),
    limit: int | None = typer.Option(None, "--limit", "-l", help="Limit number of results"),
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
            else:
                # Resolve scope input to full path
                scope = resolve_scope_input(scope, auth, client, config)

            roles_data = client.list_resource_role_assignments(scope, limit=limit)
            console.print(f"\n[bold green]Eligible Resource Roles (Scope: {scope})[/bold green]")
        else:
            roles_data = client.list_role_assignments(limit=limit)
            console.print("\n[bold green]Eligible Azure AD Roles[/bold green]")

        # Show backend info in verbose mode
        if verbose:
            backend = os.environ.get("AZ_PIM_BACKEND", DEFAULT_BACKEND)
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

            for idx, (alias_role, alias_config) in enumerate(
                zip(alias_roles, alias_configs), start=1
            ):
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

                # If the user didn't specify --resource but the selected role looks like an
                # Azure RBAC role (ARM roleDefinitionId + non-directory scope), activate via ARM.
                inferred_resource = (
                    (not resource)
                    and bool(selected_role.scope)
                    and selected_role.scope != "/"
                    and selected_role.id.startswith(
                        "/providers/Microsoft.Authorization/roleDefinitions/"
                    )
                )

                if resource or inferred_resource:
                    if inferred_resource and not resource:
                        scope = scope or selected_role.scope.lstrip("/")

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
    role: str | None = typer.Argument(
        None,
        help="Role name, ID, alias, or #N (number from list) to activate. If omitted in a TTY, you'll be prompted to search and pick.",
    ),
    duration: float | None = typer.Option(None, "--duration", "-d", help="Duration in hours"),
    justification: str | None = typer.Option(
        None, "--justification", "-j", help="Justification for activation"
    ),
    resource: bool = typer.Option(
        False, "--resource", "-r", help="Activate resource role instead of directory role"
    ),
    scope: str | None = typer.Option(None, "--scope", "-s", help="Scope for resource roles"),
    ticket: str | None = typer.Option(None, "--ticket", "-t", help="Ticket number"),
    ticket_system: str | None = typer.Option(None, "--ticket-system", help="Ticket system name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Activate a role."""
    try:
        from az_pim_cli.models import alias_to_normalized_role

        auth = AzureAuth()
        client = PIMClient(auth, verbose=verbose)
        config = Config()

        role_id: str | None = None
        role_input: str | None = role

        def is_interactive() -> bool:
            try:
                return sys.stdin.isatty()
            except Exception:
                return False

        def ensure_scope(current_scope: str | None) -> str:
            """Ensure a valid scope is provided, prompting if necessary."""
            if current_scope:
                resolved = resolve_scope_input(current_scope, auth, client, config)
                if isinstance(resolved, str):
                    return resolved

            default_sub = auth.get_subscription_id()
            default_scope = f"subscriptions/{default_sub}"
            if is_interactive():
                result = typer.prompt("Enter scope", default=default_scope)
                return str(result) if result else default_scope
            return default_scope

        def ensure_ticket_fields() -> tuple[str | None, str | None]:
            if (ticket and ticket_system) or (not ticket and not ticket_system):
                return ticket, ticket_system

            if not is_interactive():
                # Non-interactive: don't surprise with prompts; ignore incomplete ticket info.
                return None, None

            if ticket and not ticket_system:
                return ticket, typer.prompt("Ticket system name")
            if ticket_system and not ticket:
                return typer.prompt("Ticket number"), ticket_system

            return None, None

        def looks_like_arm_role_definition_id(value: str) -> bool:
            return value.startswith("/providers/Microsoft.Authorization/roleDefinitions/")

        def load_aliases() -> tuple[list[NormalizedRole], list[dict[str, Any]]]:
            alias_roles: list[NormalizedRole] = []
            alias_configs: list[dict[str, Any]] = []
            aliases = config.list_aliases()
            for alias_name, alias_config in aliases.items():
                alias_role = alias_to_normalized_role(alias_name, alias_config)
                alias_roles.append(alias_role)
                alias_configs.append(alias_config)
            return alias_roles, alias_configs

        def display_roles(
            alias_roles: list[NormalizedRole],
            alias_configs: list[dict[str, Any]],
            azure_roles: list[NormalizedRole],
            show_full_scope: bool = False,
        ) -> None:
            if alias_roles:
                console.print("[bold green]Configured Aliases[/bold green]")
                alias_table = Table(show_header=True, header_style="bold magenta")
                alias_table.add_column("#", style="bold white", justify="right", width=4)
                alias_table.add_column("Alias", style="cyan")
                alias_table.add_column("Role", style="yellow")
                alias_table.add_column("Duration", style="green")
                alias_table.add_column("Description", style="dim")
                alias_table.add_column("Scope", style="dim")

                for idx, (alias_role, alias_config) in enumerate(
                    zip(alias_roles, alias_configs), start=1
                ):
                    alias_name = alias_role.alias_name or "Unknown"
                    role_name = alias_role.name
                    duration_display = alias_role.end_time if alias_role.end_time else "-"
                    description = alias_config.get("justification", "-") if alias_config else "-"
                    scope_display = alias_role.resource_name or (
                        alias_role.scope if show_full_scope else alias_role.get_short_scope()
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

                for idx, role_item in enumerate(azure_roles, start=len(alias_roles) + 1):
                    resource_display = role_item.resource_name or (
                        role_item.scope if show_full_scope else role_item.get_short_scope()
                    )
                    resource_type_display = role_item.resource_type or "-"
                    membership_display = role_item.membership_type or "Eligible"
                    condition_display = role_item.condition if role_item.condition else "-"
                    end_time_display = role_item.end_time if role_item.end_time else "-"

                    roles_table.add_row(
                        str(idx),
                        role_item.name,
                        resource_display,
                        resource_type_display,
                        membership_display,
                        condition_display,
                        end_time_display,
                    )

                console.print(roles_table)

        # If no role was provided, run interactive picker (TTY only)
        if role_input is None:
            if not is_interactive():
                console.print("[red]Role name or ID is required in non-interactive mode.[/red]")
                raise typer.Exit(1)

            console.print(
                "[bold blue]No role provided. Fetching aliases and eligible roles...[/bold blue]"
            )

            alias_roles, alias_configs = load_aliases()

            if resource:
                scope = ensure_scope(scope)
                roles_data = client.list_resource_role_assignments(scope)
                console.print(
                    f"\n[bold green]Eligible Resource Roles (Scope: {scope})[/bold green]"
                )
            else:
                roles_data = client.list_role_assignments()
                console.print("\n[bold green]Eligible Azure AD Roles[/bold green]")

            azure_roles = normalize_roles(roles_data, source=RoleSource.ARM)
            all_roles: list[NormalizedRole] = alias_roles + azure_roles

            if not all_roles:
                console.print("[yellow]No eligible roles or aliases found.[/yellow]")
                raise typer.Exit(1)

            console.print(
                f"[dim]Found {len(alias_roles)} alias(es) and {len(azure_roles)} Azure role(s)[/dim]\n"
            )

            # Display all roles first
            display_roles(alias_roles, alias_configs, azure_roles)

            console.print()
            console.print(
                "[dim]Enter a number to activate, or a name/alias to filter (fuzzy matching enabled), or press Enter to cancel.[/dim]"
            )
            selection = typer.prompt("Select", default="")

            if not selection:
                console.print("[yellow]Selection cancelled.[/yellow]")
                raise typer.Exit(0)

            selected_role: NormalizedRole | None = None

            # Check if input is a number
            try:
                role_idx = int(selection) - 1
                if 0 <= role_idx < len(all_roles):
                    selected_role = all_roles[role_idx]
                else:
                    console.print(
                        f"[red]Invalid role number. Valid range: 1-{len(all_roles)}[/red]"
                    )
                    raise typer.Exit(1)
            except ValueError:
                # Not a number, treat as search term
                try:
                    from rapidfuzz import fuzz

                    has_rapidfuzz = True
                except ImportError:
                    has_rapidfuzz = False

                fuzzy_threshold = config.get_default("fuzzy_threshold", 0.6)
                fuzzy_threshold_float = (
                    float(fuzzy_threshold) if fuzzy_threshold is not None else 0.6
                )

                # Filter matches based on fuzzy matching
                matched_roles: list[tuple[int, NormalizedRole, float]] = []
                for idx, role_item in enumerate(all_roles):
                    if not isinstance(role_item, NormalizedRole):
                        continue
                    role_name = role_item.alias_name or role_item.name
                    if has_rapidfuzz:
                        score = fuzz.ratio(selection.lower(), role_name.lower()) / 100.0
                    else:
                        import difflib

                        score = difflib.SequenceMatcher(
                            None, selection.lower(), role_name.lower()
                        ).ratio()

                    if score >= fuzzy_threshold_float or selection.lower() in role_name.lower():
                        matched_roles.append((idx, role_item, score))

                if not matched_roles:
                    console.print(f"[yellow]No roles match '{selection}'[/yellow]")
                    raise typer.Exit(0)

                # Sort by score descending
                matched_roles.sort(key=lambda x: x[2], reverse=True)

                console.print(f"\n[green]Found {len(matched_roles)} matching role(s)[/green]\n")

                # Build filtered display lists
                filtered_alias_roles: list[NormalizedRole] = []
                filtered_alias_configs: list[dict[str, Any]] = []
                filtered_azure_roles: list[NormalizedRole] = []
                renumbered_roles: list[NormalizedRole] = []

                for _orig_idx, role_item, _score in matched_roles:
                    if not isinstance(role_item, NormalizedRole):
                        continue
                    renumbered_roles.append(role_item)
                    if getattr(role_item, "is_alias", False):
                        # Find the alias config by matching the role object
                        for i, ar in enumerate(alias_roles):
                            if ar is role_item:
                                filtered_alias_roles.append(role_item)
                                filtered_alias_configs.append(alias_configs[i])
                                break
                    else:
                        filtered_azure_roles.append(role_item)

                # Display filtered results with renumbering
                if filtered_alias_roles:
                    console.print("[bold green]Matching Aliases[/bold green]")
                    alias_table = Table(show_header=True, header_style="bold magenta")
                    alias_table.add_column("#", style="bold white", justify="right", width=4)
                    alias_table.add_column("Alias", style="cyan")
                    alias_table.add_column("Role", style="yellow")
                    alias_table.add_column("Duration", style="green")
                    alias_table.add_column("Description", style="dim")
                    alias_table.add_column("Scope", style="dim")

                    for idx, (alias_role, alias_config) in enumerate(
                        zip(filtered_alias_roles, filtered_alias_configs), start=1
                    ):
                        alias_name = alias_role.alias_name or "Unknown"
                        role_name = alias_role.name
                        duration_display = alias_role.end_time if alias_role.end_time else "-"
                        description = (
                            alias_config.get("justification", "-") if alias_config else "-"
                        )
                        scope_display = alias_role.resource_name or alias_role.get_short_scope()

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

                if filtered_azure_roles:
                    role_type = "Matching Resource Roles" if resource else "Matching Azure AD Roles"
                    console.print(f"[bold green]{role_type}[/bold green]")

                    roles_table = Table(show_header=True, header_style="bold magenta")
                    roles_table.add_column("#", style="bold white", justify="right", width=4)
                    roles_table.add_column("Role", style="cyan")
                    roles_table.add_column("Resource", style="yellow")
                    roles_table.add_column("Resource type", style="dim")

                    start_num = len(filtered_alias_roles) + 1
                    for idx, role_item in enumerate(filtered_azure_roles, start=start_num):
                        resource_display = role_item.resource_name or role_item.get_short_scope()
                        resource_type_display = role_item.resource_type or "-"

                        roles_table.add_row(
                            str(idx),
                            role_item.name,
                            resource_display,
                            resource_type_display,
                        )

                    console.print(roles_table)

                console.print()
                num_selection = typer.prompt(
                    "Enter role number to activate (or press Enter to cancel)", default=""
                )

                if not num_selection:
                    console.print("[yellow]Selection cancelled.[/yellow]")
                    raise typer.Exit(0)

                try:
                    filtered_idx = int(num_selection) - 1
                    if 0 <= filtered_idx < len(renumbered_roles):
                        selected_role = renumbered_roles[filtered_idx]
                    else:
                        console.print(
                            f"[red]Invalid selection. Valid range: 1-{len(renumbered_roles)}[/red]"
                        )
                        raise typer.Exit(1)
                except ValueError:
                    console.print("[red]Invalid input. Please enter a number.[/red]")
                    raise typer.Exit(1)

            if not selected_role:
                console.print("[red]Invalid selection.[/red]")
                raise typer.Exit(1)

            # If the selected role is an alias, delegate to alias handling; otherwise use its ID
            if getattr(selected_role, "is_alias", False):
                role_input = selected_role.alias_name or selection
            else:
                role_id = selected_role.id
                role_input = selected_role.name
                console.print(f"[green]Selected:[/green] {selected_role.name}")

                if (not resource) and selected_role.scope and selected_role.scope != "/":
                    if selected_role.id.startswith(
                        "/providers/Microsoft.Authorization/roleDefinitions/"
                    ):
                        resource = True
                        scope = scope or selected_role.scope.lstrip("/")

        # Check if role is a number reference (e.g., "#1" or "1")
        if role_input and (role_input.startswith("#") or role_input.isdigit()):
            try:
                role_num = int(role_input.lstrip("#"))
            except ValueError:
                console.print(
                    f"[red]Invalid role number format: '{role_input}'. Expected a number like '1' or '#1'.[/red]"
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
                role_input = selected_role.alias_name or role_input
            else:
                role_id = selected_role.id
                console.print(f"[green]Selected:[/green] {selected_role.name}")

                # If the selection looks like an Azure RBAC role, route activation through the
                # ARM resource-role path even if --resource wasn't specified.
                if (not resource) and selected_role.scope and selected_role.scope != "/":
                    if role_id.startswith("/providers/Microsoft.Authorization/roleDefinitions/"):
                        resource = True
                        scope = scope or selected_role.scope.lstrip("/")

        # Check if role is an alias
        alias = config.get_alias(role_input) if role_input and not role_id else None
        if alias:
            console.print(f"[blue]Using alias '[bold]{role_input}[/bold]'[/blue]")

            # Get role from alias, prompt if missing
            role_id = alias.get("role")
            if not role_id:
                console.print("[yellow]Alias is missing 'role' field.[/yellow]")
                if is_interactive():
                    role_id = typer.prompt("Enter role name or ID")
                else:
                    console.print(
                        "[red]Role name or ID is required when using an alias without a 'role'. Pass a role or update the alias configuration.[/red]"
                    )
                    raise typer.Exit(1)

            # Merge alias defaults with command-line overrides
            duration = duration or parse_duration_from_alias(alias.get("duration"))
            justification = justification or alias.get("justification")

            # Handle scope from alias
            if alias and "scope" in alias:
                alias_scope = alias.get("scope")
                if alias_scope == "subscription":
                    resource = True
                    subscription = alias.get("subscription")
                    if not subscription:
                        # Prompt for subscription if missing (TTY) or use current subscription (non-TTY)
                        if is_interactive():
                            subscription = typer.prompt(
                                "Enter subscription ID", default=auth.get_subscription_id()
                            )
                        else:
                            subscription = auth.get_subscription_id()
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
                if is_interactive():
                    scope = typer.prompt("Enter scope", default=f"subscriptions/{default_sub}")
                else:
                    scope = f"subscriptions/{default_sub}"
        elif not role_id:
            role_id = role_input

        # If activating a resource role, prompt/derive missing info and resolve role names.
        if resource:
            if not scope:
                subscription_id = auth.get_subscription_id()
                scope = f"subscriptions/{subscription_id}"
            else:
                scope = ensure_scope(scope)

            if role_id and not looks_like_arm_role_definition_id(role_id):
                # Resolve a display name (e.g., "Owner") to the roleDefinitionId at this scope.
                resolver = get_resolver(config)

                def fetch_roles() -> list[NormalizedRole]:
                    """Fetch roles for the scope."""
                    if not scope:
                        return []
                    roles_data = client.list_resource_role_assignments(scope)
                    return normalize_roles(roles_data, source=RoleSource.ARM)

                resolved_role = resolve_role(
                    resolver=resolver,
                    role_input=role_id,
                    scope=scope,
                    fetch_roles_fn=fetch_roles,
                    role_name_extractor=lambda r: r.name,
                )

                if not resolved_role:
                    console.print(
                        "[yellow]Tip:[/yellow] Run 'az-pim list --resource --scope <scope>' to see all available roles."
                    )
                    raise typer.Exit(1)

                role_id = resolved_role.id

        # Prompt for missing required inputs with defaults implied by TTY
        if is_interactive() and duration is None:
            # Suggest default duration from config (e.g., PT8H) or fallback to 8 hours
            default_dur = parse_duration_from_alias(config.get_default("duration")) or 8.0
            dur_input = typer.prompt("Enter duration (hours)", default=str(int(default_dur)))
            try:
                duration = float(dur_input)
            except ValueError:
                console.print(
                    "[red]Invalid duration. Please enter a number of hours (e.g., 8).[/red]"
                )
                raise typer.Exit(1)

        if is_interactive() and not justification:
            default_just = config.get_default("justification") or "Requested via az-pim-cli"
            justification = typer.prompt("Enter justification", default=default_just)

        duration_str = get_duration_string(duration)
        justification = (
            justification or config.get_default("justification") or "Requested via az-pim-cli"
        )

        ticket_value, ticket_system_value = ensure_ticket_fields()

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
                ticket_number=ticket_value,
                ticket_system=ticket_system_value,
            )
        else:
            console.print()
            result = client.request_role_activation(
                role_definition_id=role_id,
                duration=duration_str,
                justification=justification,
                ticket_number=ticket_value,
                ticket_system=ticket_system_value,
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
    scope: str | None = typer.Option(
        None, "--scope", "-s", help="Scope for resource roles (e.g., subscriptions/{id})"
    ),
) -> None:
    """View activation history."""
    try:
        auth = AzureAuth()
        client = PIMClient(auth)
        config = Config()

        console.print(f"[bold blue]Fetching activation history (last {days} days)...[/bold blue]")

        if resource:
            if not scope:
                subscription_id = auth.get_subscription_id()
                scope = f"subscriptions/{subscription_id}"
            else:
                # Resolve scope input to full path
                scope = resolve_scope_input(scope, auth, client, config)
            activations = client.list_resource_activation_history(scope=scope, days=days)
        else:
            activations = client.list_activation_history(days=days)

        if not activations:
            console.print("[yellow]No activation history found.[/yellow]")
            return

        title = "Resource Role Activation History" if resource else "Activation History"
        console.print(f"\n[bold green]{title}[/bold green]\n")

        table = Table(show_header=True, header_style="bold magenta")
        if resource:
            table.add_column("Role", style="cyan")
            table.add_column("Scope", style="dim")
            table.add_column("Request Type", style="dim")
            table.add_column("Status", style="green")
            table.add_column("Created", style="dim")

            for req in activations:
                props = req.get("properties", {})
                expanded = props.get("expandedProperties", {})
                role_def = expanded.get("roleDefinition", {})
                role_name = role_def.get("displayName") or props.get("roleDefinitionId", "Unknown")
                req_scope = props.get("scope", scope or "")
                request_type = props.get("requestType", "N/A")
                status = props.get("status", "N/A")
                created = props.get("createdOn", "N/A")

                table.add_row(role_name, req_scope, request_type, status, created)
        else:
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
        raise typer.Exit(1)


@app.command("approve")
def approve_request(
    request_id: str = typer.Argument(..., help="Request ID to approve"),
    justification: str | None = typer.Option(
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
    role: str | None = typer.Argument(None, help="Role name or ID"),
    duration: str | None = typer.Option(None, "--duration", "-d", help="Duration (e.g., PT8H)"),
    justification: str | None = typer.Option(None, "--justification", "-j", help="Justification"),
    scope: str | None = typer.Option(None, "--scope", "-s", help="Scope (directory, subscription)"),
    subscription: str | None = typer.Option(None, "--subscription", help="Subscription ID"),
    resource: str | None = typer.Option(None, "--resource", help="Resource name"),
    resource_type: str | None = typer.Option(None, "--resource-type", help="Resource type"),
    membership: str | None = typer.Option(None, "--membership", help="Membership type"),
    condition: str | None = typer.Option(None, "--condition", help="Condition expression"),
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


@app.command("whoami")
def whoami(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Show current Azure identity and authentication information."""
    try:
        auth = AzureAuth()

        console.print("\n[bold cyan]🔐 Azure Identity Information[/bold cyan]\n")

        # Get tenant ID
        try:
            tenant_id = auth.get_tenant_id()
            console.print(f"[bold]Tenant ID:[/bold] [green]{tenant_id}[/green]")
        except Exception as e:
            console.print(f"[bold]Tenant ID:[/bold] [red]Unable to retrieve ({str(e)})[/red]")

        # Get user object ID
        try:
            user_id = auth.get_user_object_id()
            console.print(f"[bold]User Object ID:[/bold] [green]{user_id}[/green]")
        except Exception as e:
            console.print(f"[bold]User Object ID:[/bold] [red]Unable to retrieve ({str(e)})[/red]")

        # Get subscription ID
        try:
            subscription_id = auth.get_subscription_id()
            console.print(f"[bold]Current Subscription:[/bold] [green]{subscription_id}[/green]")
        except Exception as e:
            console.print(
                f"[bold]Current Subscription:[/bold] [yellow]Not available ({str(e)})[/yellow]"
            )

        # Show auth mode
        console.print("\n[bold]Authentication Mode:[/bold] [cyan]Azure CLI Credential[/cyan]")
        console.print(
            "[dim]Using Azure CLI login (az login). "
            "Fallback to DefaultAzureCredential if Azure CLI is not available.[/dim]"
        )

        # Show IPv4-only mode
        if should_use_ipv4_only():
            console.print("\n[bold]Network Mode:[/bold] [yellow]IPv4-only mode enabled[/yellow]")

        # Show backend
        backend = os.environ.get("AZ_PIM_BACKEND", DEFAULT_BACKEND)
        console.print(f"[bold]Backend:[/bold] [cyan]{backend}[/cyan]")

        if verbose:
            console.print("\n[bold cyan]Token Validation:[/bold cyan]")
            try:
                # Validate Graph token availability
                auth.get_token("https://graph.microsoft.com/.default")
                console.print("[dim]✓ Graph API token available[/dim]")
            except Exception as e:
                console.print(f"[dim]✗ Graph API token: [red]Failed ({str(e)})[/red][/dim]")

            try:
                # Validate ARM token availability
                auth.get_token("https://management.azure.com/.default")
                console.print("[dim]✓ ARM API token available[/dim]")
            except Exception as e:
                console.print(f"[dim]✗ ARM API token: [red]Failed ({str(e)})[/red][/dim]")

        console.print()

    except AuthenticationError as e:
        console.print(f"\n[red]✗ Authentication failed: {str(e)}[/red]")
        if hasattr(e, "suggestion") and e.suggestion:
            console.print(f"[yellow]Suggestion: {e.suggestion}[/yellow]\n")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[red]✗ Error: {str(e)}[/red]\n")
        if verbose:
            import traceback

            console.print(f"[dim]{traceback.format_exc()}[/dim]")
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
