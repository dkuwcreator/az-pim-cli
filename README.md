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
```

### Activate a Role

```bash
# Activate an Azure AD role
az-pim activate "Global Administrator" --duration 8 --justification "Emergency access"

# Activate a resource role
az-pim activate "{role-id}" --resource --scope "subscriptions/{sub-id}" --duration 4

# Activate with ticket information
az-pim activate "Security Admin" --duration 2 --ticket "INC123456" --ticket-system "ServiceNow"
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

## Troubleshooting

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

### Permission Errors

Ensure your account has:
- PIM role eligibility for the roles you want to activate
- Appropriate approval permissions for approving requests

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
