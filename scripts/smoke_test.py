#!/usr/bin/env python3
"""Smoke test for az-pim-cli.

This script performs basic validation of the CLI functionality:
1. Acquires authentication token
2. Calls one Graph GET endpoint (list eligible Entra roles)
3. Prints results in a Rich table
4. Exits with status code 0 (success) or 1 (failure)

Usage:
    python scripts/smoke_test.py
    # or
    make smoke
"""

import sys
from pathlib import Path

# Add src to path for development
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from rich.console import Console
from rich.table import Table

from az_pim_cli.auth import AzureAuth
from az_pim_cli.exceptions import AuthenticationError, NetworkError, PermissionError
from az_pim_cli.providers.entra_graph import EntraGraphProvider

console = Console()


def main() -> int:
    """Run smoke test."""
    console.print("\n[bold cyan]🔍 az-pim-cli Smoke Test[/bold cyan]\n")

    # Step 1: Authentication
    console.print("Step 1: Authenticating with Azure...")
    try:
        auth = AzureAuth()
        tenant_id = auth.get_tenant_id()
        user_id = auth.get_user_object_id()
        console.print(f"  ✓ Authenticated as user [green]{user_id}[/green]")
        console.print(f"  ✓ Tenant: [green]{tenant_id}[/green]")
    except AuthenticationError as e:
        console.print(f"  [red]✗ Authentication failed: {e.message}[/red]")
        if e.suggestion:
            console.print(f"  [yellow]Suggestion: {e.suggestion}[/yellow]")
        return 1
    except Exception as e:
        console.print(f"  [red]✗ Unexpected error: {e}[/red]")
        return 1

    # Step 2: Test Graph API call
    console.print("\nStep 2: Testing Graph API (list eligible Entra roles)...")
    try:
        provider = EntraGraphProvider(auth=auth, verbose=False)
        roles = provider.list_eligible_roles(limit=5)  # Limit to 5 for smoke test
        console.print(f"  ✓ Retrieved [green]{len(roles)}[/green] eligible Entra roles")
    except PermissionError as e:
        console.print(f"  [red]✗ Permission denied: {e.message}[/red]")
        console.print(f"  [yellow]Required permissions: {', '.join(e.required_permissions)}[/yellow]")
        return 1
    except NetworkError as e:
        console.print(f"  [red]✗ Network error: {e.message}[/red]")
        if e.suggest_ipv4:
            console.print("  [yellow]Suggestion: Try setting AZ_PIM_IPV4_ONLY=1[/yellow]")
        return 1
    except Exception as e:
        console.print(f"  [red]✗ Unexpected error: {e}[/red]")
        return 1

    # Step 3: Display results in Rich table
    console.print("\nStep 3: Displaying results...\n")
    table = Table(title="Eligible Entra Roles (Sample)", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Role Name", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Role Definition ID", style="dim", overflow="fold")

    for idx, role in enumerate(roles[:5], 1):  # Show max 5 roles
        role_def = role.get("roleDefinition", {})
        role_name = role_def.get("displayName", "Unknown")
        role_id = role.get("roleDefinitionId", "N/A")
        status = role.get("status", "Unknown")

        table.add_row(str(idx), role_name, status, role_id)

    console.print(table)

    # Summary
    console.print("\n[bold green]✓ Smoke test passed successfully![/bold green]")
    console.print("\nNext steps:")
    console.print("  • Run full test suite: [cyan]pytest[/cyan]")
    console.print("  • Try listing roles: [cyan]az-pim list[/cyan]")
    console.print("  • Check documentation: [cyan]docs/API_MAP.md[/cyan]\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
