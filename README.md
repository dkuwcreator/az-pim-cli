# az-pim-cli

A lightweight Python + Typer CLI for Azure Privileged Identity Management (PIM). Request or approve roles, view history, and define custom aliases with preset options like duration, description, and scope.

## Features

- 🔐 **Azure AD Roles**: Request and manage Azure AD (Entra ID) privileged roles
- ☁️ **Resource Roles**: Request and manage Azure resource roles (subscriptions, resource groups)
- ⚡ **Quick Activation**: Activate roles with simple commands
- 🎯 **Smart Input Resolution**: Intelligent matching for role/scope names with fuzzy search support
- 📝 **Approval Workflow**: Approve pending role requests
- 📊 **History Tracking**: View activation history
- 🏷️ **Aliases**: Define custom aliases with preset duration, justification, and scope
- 🔑 **Flexible Auth**: Uses Azure CLI credentials or MSAL for authentication
- 🎨 **Rich UI**: Beautiful terminal output with tables and colors
- 💾 **Smart Caching**: Caches role lookups to minimize API calls

## Installation

### From Source

```bash
git clone https://github.com/dkuwcreator/az-pim-cli.git
cd az-pim-cli
pip install -e .
```

### Optional: Enhanced Fuzzy Matching

For better performance with fuzzy name matching:

```bash
pip install az-pim-cli[fuzzy]
```

This installs `rapidfuzz` for faster and more accurate fuzzy matching.

### From PyPI (coming soon)

```bash
pip install az-pim-cli
# Or with fuzzy matching support
pip install az-pim-cli[fuzzy]
```

## Prerequisites

- Python 3.10 or higher
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

### Smart Input Resolution

The CLI intelligently matches role and scope names, so you don't need to type exact names:

```bash
# Partial names (prefix matching)
az-pim activate "Contrib"  # Matches "Contributor"
az-pim activate "Sec Admin"  # Matches "Security Administrator"

# Case-insensitive
az-pim activate "owner"  # Matches "Owner"

# Typo correction (fuzzy matching)
az-pim activate "Contributer"  # Matches "Contributor"
az-pim activate "Sec Admnistrator"  # Matches "Security Administrator"

# Scope name matching
az-pim activate "Owner" --resource --scope "Production"
# Matches subscription or resource group named "Production"

# Interactive selection with multiple matches (TTY only)
az-pim activate "Security"
# Shows numbered list:
#   1. Security Administrator
#   2. Security Reader
# Select number [1]: _
```

Configuration in `~/.az-pim-cli/config.yml`:

```yaml
defaults:
  fuzzy_matching: true      # Enable fuzzy matching
  fuzzy_threshold: 0.8      # Minimum similarity (0.0-1.0)
  cache_ttl_seconds: 300    # Cache lookups for 5 minutes
```

See [EXAMPLES.md](docs/EXAMPLES.md#smart-input-resolution) for more details.

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

#### Interactive Selection

Use interactive mode to select and activate roles:

```bash
# List roles and select interactively
az-pim list --select

# For resource roles
az-pim list --resource --select
```

#### Quick Activation by Number

All listed roles are numbered for easy reference:

```bash
# List roles to see numbers
az-pim list

# Activate by number instead of copying the full role ID
az-pim activate 1 --duration 4 --justification "Quick access"
az-pim activate "#2" --duration 2 --justification "Emergency access"
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

### Project Architecture

The project follows a clean architecture pattern with clear separation of concerns:

```
src/az_pim_cli/
├── domain/          # Pure business logic (models, exceptions)
├── app/             # Application services and use cases
├── infra/           # Infrastructure adapters (HTTP, config, auth)
├── interfaces/      # Protocol definitions (ports)
├── cli.py           # CLI entry point
├── pim_client.py    # PIM API client
├── resolver.py      # Input resolution logic
├── auth.py          # Authentication
└── config.py        # Configuration (backward compatibility)
```

**Key Design Principles:**
- **Domain Layer**: Contains pure business logic with no external dependencies
- **Infrastructure Layer**: Adapters for external services (HTTP, file system, cloud APIs)
- **Interfaces**: Protocol definitions allowing swappable implementations
- **Backward Compatibility**: Original modules re-export from new locations

### Setup Development Environment

```bash
git clone https://github.com/dkuwcreator/az-pim-cli.git
cd az-pim-cli
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Development Tools

The project uses modern Python tooling:

- **ruff**: Fast linter and formatter (replaces black + isort + flake8)
- **mypy**: Static type checking with strict mode
- **pytest**: Testing framework with coverage
- **pre-commit**: Automated code quality checks

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=az_pim_cli

# Run specific test file
pytest tests/test_config.py -v
```

### Code Quality

```bash
# Format code
ruff format src/ tests/

# Lint code (with auto-fix)
ruff check --fix src/ tests/

# Type check
mypy src/

# Run pre-commit hooks manually
pre-commit run --all-files
```

### Configuration Options

The CLI supports enhanced configuration via Pydantic models:

**File-based** (`~/.az-pim-cli/config.yml`):
```yaml
aliases:
  prod-admin:
    role: "Contributor"
    duration: "PT4H"
    justification: "Production deployment"
    scope: "subscription"
    subscription: "{sub-id}"

defaults:
  duration: "PT8H"
  justification: "Requested via az-pim-cli"
  fuzzy_matching: true
  fuzzy_threshold: 0.8
  cache_ttl_seconds: 300
```

**Environment Variables**:
```bash
export AZ_PIM_IPV4_ONLY=1       # Force IPv4-only DNS
export AZ_PIM_BACKEND=ARM       # API backend (ARM/GRAPH)
export AZ_PIM_VERBOSE=true      # Enable verbose logging
```

### Architecture Benefits

1. **Swappable Components**: HTTP client and config adapters can be replaced
2. **Type Safety**: Pydantic validation catches configuration errors early
3. **Testability**: Clean separation makes unit testing easier
4. **Maintainability**: Clear boundaries reduce coupling
5. **Backward Compatibility**: Existing code continues to work

## Development

### Setup Development Environment

```bash

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

See [CHANGELOG.md](CHANGELOG.md) for recent changes and [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

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
