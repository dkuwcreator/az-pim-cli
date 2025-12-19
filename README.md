# az-pim-cli v2.0

A lightweight Python + Typer CLI for Azure Privileged Identity Management (PIM). Three focused commands for better organization and clarity:

- **`azp-res`**: Manage Azure resource roles (ARM-scoped)
- **`azp-entra`**: Manage Entra ID directory roles (Graph-scoped)
- **`azp-groups`**: Manage Entra group memberships (Graph-scoped)

## Key Features

- **Clearer scope management**: Each command uses the appropriate OAuth scope (ARM or Graph)
- **Better error messages**: Tailored permission hints for each PIM type
- **Improved organization**: Commands are grouped by PIM subject
- **Explicit scope control**: No ambiguous scope logic

## Features

- 🔐 **Entra Roles** (`azp-entra`): Manage Entra ID (formerly Azure AD) privileged directory roles
- ☁️ **Resource Roles** (`azp-res`): Manage Azure resource roles (subscriptions, resource groups)
- 👥 **Group Memberships** (`azp-groups`): Manage PIM for Groups assignments
- ⚡ **Quick Activation**: Activate roles with simple commands
- 📝 **Approval Workflow**: Approve pending role requests
- 📊 **History Tracking**: View activation history
- 🎯 **Aliases**: Define custom aliases with preset duration, justification, and scope
- 🔑 **Flexible Auth**: Uses Azure CLI credentials or Azure Identity SDK
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

### Command Reference Table

| PIM Type | Command | OAuth Scope | Required Permissions |
|----------|---------|-------------|---------------------|
| Azure Resources (RBAC) | `azp-res` | ARM | Reader + eligible PIM role |
| Entra Directory Roles | `azp-entra` | Graph | PrivilegedAccess.Read.AzureAD |
| Entra Group Memberships | `azp-groups` | Graph | PrivilegedAccess.Read.AzureADGroup |

### Azure Resources (`azp-res`)

Manage Azure resource roles like Owner, Contributor, Reader for subscriptions and resource groups.

```bash
# List eligible resource roles for current subscription
azp-res list

# List for specific scope
azp-res list --scope "subscriptions/{subscription-id}"

# Activate a resource role
azp-res activate "{role-id}" --duration 4 --justification "Production deployment"

# With ticket information
azp-res activate "{role-id}" --duration 2 --ticket "INC123456" --ticket-system "ServiceNow"
```

### Entra Directory Roles (`azp-entra`)

Manage Entra ID (formerly Azure AD) directory roles like Global Administrator, Security Administrator.

```bash
# List eligible Entra roles
azp-entra list

# Activate an Entra role
azp-entra activate "{role-id}" --duration 2 --justification "Emergency access"

# View activation history
azp-entra history --days 7

# List pending approval requests
azp-entra pending

# Approve a request
azp-entra approve {request-id} --justification "Approved for maintenance"
```

### Entra Group Memberships (`azp-groups`)

Manage PIM for Groups assignments (Entra ID security groups).

```bash
# List eligible group assignments
azp-groups list

# Activate a group membership
azp-groups activate "{group-id}" --access member --duration 4

# Activate as owner
azp-groups activate "{group-id}" --access owner --duration 2

# View group activation history
azp-groups history
```

## Verbose Logging

All commands support `--verbose` flag to show:
- OAuth scope being used (ARM/Graph)
- Backend hint
- IPv4-only mode status
- Detailed error traces

```bash
azp-res list --verbose
azp-entra activate "{role-id}" --verbose
```

## Configuration

The CLI stores configuration in `~/.az-pim-cli/config.yml`. 

### Aliases with Prefixes

Aliases now use prefixes to identify which command they're for:

```yaml
aliases:
  res:prod-owner:
    role: "/subscriptions/{sub-id}/providers/Microsoft.Authorization/roleDefinitions/{role-id}"
    duration: "PT4H"
    justification: "Production environment access"
    scope: "subscriptions/{subscription-id}"
  
  entra:emergency:
    role: "Global Administrator"
    duration: "PT2H"
    justification: "Emergency access"
    scope: "directory"
  
  groups:security-team:
    group_id: "{group-id}"
    access: "member"
    duration: "PT8H"
    justification: "Security operations"

defaults:
  duration: "PT8H"
  justification: "Requested via az-pim-cli"
```

### Using Aliases

```bash
# Use a resource alias
azp-res activate prod-owner

# Use an Entra role alias
azp-entra activate emergency

# Use a groups alias
azp-groups activate security-team
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
2. **Azure Identity SDK**: Falls back to DefaultAzureCredential (supports managed identity, service principal, etc.)

Make sure you're logged in with appropriate permissions:

```bash
az login
az account show
```

## Advanced Configuration

### Environment Variables

#### IPv4-Only Mode

If you experience DNS resolution issues (especially with IPv6), enable IPv4-only mode:

```bash
export AZ_PIM_IPV4_ONLY=1
azp-res list
```

This forces all network connections to use IPv4, which can resolve DNS issues on some networks.

#### Verbose Output

Enable verbose output for debugging:

```bash
azp-res list --verbose
azp-entra activate "{role-id}" --verbose
```

Verbose mode shows:
- OAuth scope (ARM/Graph)
- Backend hint
- IPv4-only mode status
- Detailed error traces

## Troubleshooting

### DNS Resolution Failures

If you see errors like "getaddrinfo failed" or "name resolution error":

```bash
# Enable IPv4-only mode
export AZ_PIM_IPV4_ONLY=1
azp-res list
```

### Permission Errors (403)

**For `azp-res` (Azure resources):**
- Ensure you have Reader permission
- Ensure you have eligible PIM role assignments
- Check scope is correct (subscription/resource group)

**For `azp-entra` (Entra roles):**
- Ensure you have Graph permissions: `PrivilegedAccess.Read.AzureAD`
- Ensure you have eligible Entra role assignments

**For `azp-groups` (Groups):**
- Ensure you have Graph permissions: `PrivilegedAccess.Read.AzureADGroup`
- Ensure you have eligible group assignments

### Authentication Errors

If you see "token expired" or "not logged in":

```bash
# Refresh your Azure CLI login
az login

# Or force a new login
az logout
az login
```

### Version Check

```bash
azp-res version
azp-entra version
azp-groups version
```

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

## Related Projects

- [Azure CLI](https://github.com/Azure/azure-cli)
- [Azure Identity SDK](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/identity)
- [Typer](https://github.com/tiangolo/typer)

## Support

For issues and questions:
- GitHub Issues: https://github.com/dkuwcreator/az-pim-cli/issues
- Azure PIM Documentation: https://docs.microsoft.com/en-us/azure/active-directory/privileged-identity-management/
