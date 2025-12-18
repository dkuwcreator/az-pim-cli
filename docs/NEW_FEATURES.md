# Azure PIM CLI - New Features Examples

## Example 1: Using IPv4-only mode for DNS issues
```bash
# If you experience DNS resolution errors, enable IPv4-only mode
export AZ_PIM_IPV4_ONLY=1
az-pim list

# Or inline for a single command
AZ_PIM_IPV4_ONLY=1 az-pim list
```

## Example 2: Using verbose mode for debugging
```bash
# See detailed information about API calls, backends, and errors
az-pim list --verbose

# Verbose mode shows:
# - [DEBUG] PIM Client initialized with backend: ARM
# - [DEBUG] IPv4-only mode: False
# - [DEBUG] GET https://management.azure.com/...
# - [DEBUG] Response status: 200
# - Backend: ARM | IPv4-only: off
```

## Example 3: Limiting results for large role sets
```bash
# Get only the first 10 roles for quick preview
az-pim list --limit 10

# Combine with resource roles
az-pim list --resource --limit 5
```

## Example 4: Full scope display
```bash
# Default: shortened scope for readability
az-pim list
# Output: sub:12345678.../rg:my-rg

# Full scope: complete paths
az-pim list --full-scope
# Output: /subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/my-rg
```

## Example 5: Error handling improvements
```bash
# Authentication errors now provide actionable suggestions
az-pim list
# Output if not logged in:
# [bold red]Authentication Error:[/bold red] Not logged in to Azure CLI
# [yellow]Suggestion:[/yellow] Run 'az login' to authenticate with Azure

# Network errors provide helpful hints
az-pim list
# Output if DNS fails:
# [bold red]Network Error:[/bold red] Connection error during list role assignments: ...
# [yellow]💡 Tip:[/yellow] If you're experiencing DNS issues, try enabling IPv4-only mode:
#    export AZ_PIM_IPV4_ONLY=1

# Permission errors show what's missing
az-pim list
# Output if permission denied:
# [bold red]Permission Error:[/bold red] Permission denied for list role assignments. Principal ID: xxx...
# [yellow]Required permissions:[/yellow] RoleManagement.ReadWrite.Directory or equivalent Azure RBAC permissions
```

## Example 6: Backend selection (advanced)
```bash
# Use ARM API (default, recommended)
export AZ_PIM_BACKEND=ARM
az-pim list --verbose

# Use Graph API (requires additional permissions)
export AZ_PIM_BACKEND=GRAPH
az-pim list --verbose
```

## Example 7: Combined usage
```bash
# Enable IPv4, use verbose mode, and limit results
export AZ_PIM_IPV4_ONLY=1
az-pim list --verbose --limit 5 --full-scope
```

## Example 8: Pagination support
```bash
# The CLI now automatically handles pagination for large role sets
# Previously, only the first page was returned
# Now, all pages are fetched automatically (can be limited with --limit)

# Get all roles (pagination automatic)
az-pim list

# Get first 100 roles (stops pagination early)
az-pim list --limit 100
```

## Environment Variables Summary

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `AZ_PIM_IPV4_ONLY` | 1, true, yes | off | Force IPv4-only DNS resolution |
| `AZ_PIM_BACKEND` | ARM, GRAPH | ARM | Choose API backend |

## Error Types

The CLI now distinguishes between different error types:

1. **AuthenticationError**: Token expired, not logged in
   - Suggestion: Run `az login`

2. **NetworkError**: DNS, timeout, connection issues
   - Shows endpoint that failed
   - Suggests IPv4-only mode if DNS-related

3. **PermissionError**: 403 errors, authorization issues
   - Shows endpoint and principal ID
   - Lists required permissions

4. **ParsingError**: Response parsing failures
   - Shows truncated response data
   - May indicate API changes

## Migration Guide

No breaking changes! All existing commands work as before.

New opt-in features:
- Set environment variables to enable IPv4-only or change backend
- Add `--verbose`, `--limit`, or `--full-scope` flags as needed
- Error messages are now more informative automatically
