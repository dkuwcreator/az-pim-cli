# az-pim-cli

A lightweight Python + Typer CLI for Azure Privileged Identity Management (PIM). Request or approve roles, view history, and define custom aliases with preset options like duration, description, and scope.

## Features

- 🔐 **Azure AD Roles**: Request and manage Azure AD (Entra ID) privileged roles
- ☁️ **Resource Roles**: Request and manage Azure resource roles (subscriptions, resource groups)
- ⚡ **Quick Activation**: Activate roles with simple commands
- 📝 **Approval Workflow**: Approve pending role requests
- 📊 **History Tracking**: View activation history
- 🎯 **Aliases**: Define custom aliases with preset duration, justification, and scope
- 🔑 **Flexible Auth**: Uses Azure CLI credentials or MSAL for authentication
- 🎨 **Rich UI**: Beautiful terminal output with tables and colors

## Installation

### From Source

```bash
git clone https://github.com/dkuwcreator/az-pim-cli.git
cd az-pim-cli
pip install -e .
```

### From PyPI (coming soon)

```bash
pip install az-pim-cli
```

## Prerequisites

- Python 3.8 or higher
- Azure CLI installed and logged in (`az login`)
- Appropriate permissions to manage PIM roles

## Quick Start

### List Eligible Roles

```bash
# List Azure AD roles
az-pim list

# List resource roles for current subscription
az-pim list --resource

# List resource roles for specific scope
az-pim list --resource --scope "subscriptions/{subscription-id}"

# Interactive mode: select and activate a role
az-pim list --select
```

### Activate a Role

```bash
# Activate an Azure AD role
az-pim activate "Global Administrator" --duration 8 --justification "Emergency access"

# Activate a resource role
az-pim activate "{role-id}" --resource --scope "subscriptions/{sub-id}" --duration 4

# Activate with ticket information
az-pim activate "Security Admin" --duration 2 --ticket "INC123456" --ticket-system "ServiceNow"

# Activate by role number (from list output)
az-pim activate 1 --duration 4 --justification "Quick activation"
# or with # prefix
az-pim activate "#2" --duration 2 --justification "Emergency access"
```

### View Activation History

```bash
# View last 30 days
az-pim history

# View last 7 days
az-pim history --days 7
```

### Manage Aliases

Aliases allow you to save common role activation configurations:

```bash
# Add an alias
az-pim alias add prod-admin "Owner" \
  --duration "PT4H" \
  --justification "Production deployment" \
  --scope "subscription" \
  --subscription "{subscription-id}"

# List all aliases
az-pim alias list

# Use an alias to activate
az-pim activate prod-admin

# Remove an alias
az-pim alias remove prod-admin
```

### Approve Requests

```bash
# List pending approvals
az-pim pending

# Approve a request
az-pim approve {request-id} --justification "Approved for maintenance window"
```

## Configuration

The CLI stores configuration in `~/.az-pim-cli/config.yml`. You can manually edit this file to define aliases and defaults:

```yaml
aliases:
  emergency:
    role: "Global Administrator"
    duration: "PT2H"
    justification: "Emergency access"
    scope: "directory"
  
  prod-owner:
    role: "/subscriptions/{sub-id}/providers/Microsoft.Authorization/roleDefinitions/{role-id}"
    duration: "PT8H"
    justification: "Production environment access"
    scope: "subscription"
    subscription: "{subscription-id}"

defaults:
  duration: "PT8H"
  justification: "Requested via az-pim-cli"
```

## Usage Examples

### Scenario 1: Quick Azure AD Role Activation

```bash
# Activate Global Admin for 2 hours
az-pim activate "Global Administrator" -d 2 -j "Password reset for executive"
```

### Scenario 2: Resource Role with Alias

```bash
# Create an alias for common production access
az-pim alias add prod \
  "Contributor" \
  --duration "PT4H" \
  --justification "Production deployment" \
  --scope "subscription"

# Later, quickly activate using the alias
az-pim activate prod
```

### Scenario 3: Approval Workflow

```bash
# Check for pending approvals
az-pim pending

# Approve a specific request
az-pim approve {request-id} -j "Approved for scheduled maintenance"
```

## Duration Format

Durations use ISO 8601 format:
- `PT1H` = 1 hour
- `PT2H` = 2 hours
- `PT8H` = 8 hours (default)
- `PT30M` = 30 minutes

You can also use the `--duration` flag with hours as a number (e.g., `--duration 4` for 4 hours).

## Authentication

The CLI uses the following authentication methods in order:

1. **Azure CLI**: Uses your existing `az login` session
2. **MSAL**: Falls back to Azure Identity DefaultAzureCredential (supports managed identity, service principal, etc.)

Make sure you're logged in with appropriate permissions:

```bash
az login
az account show
```

## Advanced Configuration

### Environment Variables

The CLI supports several environment variables for advanced configuration:

#### IPv4-Only Mode

If you experience DNS resolution issues (especially with IPv6), enable IPv4-only mode:

```bash
export AZ_PIM_IPV4_ONLY=1
az-pim list
```

This forces all network connections to use IPv4, which can resolve DNS issues on some networks.

#### Backend Selection

Choose between ARM and Graph API backends (default is ARM):

```bash
# Use ARM API (default, recommended)
export AZ_PIM_BACKEND=ARM

# Use Graph API (requires additional permissions)
export AZ_PIM_BACKEND=GRAPH
```

The ARM backend aligns with Azure Portal behavior and works with standard Azure CLI permissions.

#### Verbose Output

Enable verbose output for debugging:

```bash
az-pim list --verbose
az-pim activate "Global Administrator" --verbose
```

Verbose mode shows:
- API endpoints being called
- Backend used (ARM/Graph)
- IPv4-only mode status
- Detailed error traces

### Additional CLI Options

#### Limit Results

Limit the number of results returned when listing roles:

```bash
# Get only the first 10 roles
az-pim list --limit 10

# Get first 5 resource roles
az-pim list --resource --limit 5
```

#### Full Scope Display

Show full scope paths instead of shortened versions:

```bash
# Short scope (default): "sub:12345678.../rg:my-resource-group"
az-pim list

# Full scope: "/subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/my-resource-group"
az-pim list --full-scope
```

## Troubleshooting

### DNS Resolution Failures

If you see errors like "getaddrinfo failed" or "name resolution error":

```bash
# Enable IPv4-only mode
export AZ_PIM_IPV4_ONLY=1
az-pim list
```

This is particularly useful on networks with IPv6 connectivity issues.

### "Failed to get tenant ID"

Make sure you're logged in with Azure CLI:
```bash
az login
az account show
```

### "No eligible roles found"

Verify you have eligible PIM role assignments:
- Check Azure Portal → Azure AD → Privileged Identity Management
- Or for resource roles: Azure Portal → Subscription → Access Control (IAM) → Eligible assignments

### Permission Errors (403)

The error message will show:
- The endpoint that failed
- Your principal ID
- Required permissions

Common causes:
- Missing RoleManagement.ReadWrite.Directory permission for Azure AD roles
- Missing Azure RBAC permissions for resource roles
- Not logged in or expired token

Solutions:
```bash
# Refresh your login
az login

# Check your account
az account show

# Verify you have the right permissions in Azure Portal
```

### Authentication Errors

If you see "token expired" or "not logged in":

```bash
# Refresh your Azure CLI login
az login

# Or force a new login
az logout
az login
```

### Network Timeouts

For network timeout errors:
1. Check your internet connection
2. Try enabling IPv4-only mode: `export AZ_PIM_IPV4_ONLY=1`
3. Check if your firewall/proxy is blocking Azure endpoints

### Parsing Errors

If you encounter response parsing errors, this may indicate:
- API changes or instability
- Network issues causing truncated responses
- Try using verbose mode to see the full response: `--verbose`

## Development

### Setup Development Environment

```bash
git clone https://github.com/dkuwcreator/az-pim-cli.git
cd az-pim-cli
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
pytest --cov=az_pim_cli
```

### Code Formatting

```bash
black src/
flake8 src/
mypy src/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Roadmap

- [ ] Support for PIM for Groups
- [ ] Interactive mode for role selection
- [ ] Export history to CSV/JSON
- [ ] Role assignment schedule management
- [ ] Multi-tenant support
- [ ] Shell completion (bash, zsh, fish)

## Related Projects

- [Azure CLI](https://github.com/Azure/azure-cli)
- [Azure Identity SDK](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/identity)
- [Typer](https://github.com/tiangolo/typer)

## Support

For issues and questions:
- GitHub Issues: https://github.com/dkuwcreator/az-pim-cli/issues
- Azure PIM Documentation: https://docs.microsoft.com/en-us/azure/active-directory/privileged-identity-management/
