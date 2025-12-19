# Example Configuration

This file shows example configurations for the Azure PIM CLI.

## Configuration File Location

The configuration file is stored at: `~/.az-pim-cli/config.yml`

## Example Configuration

```yaml
# Default settings
defaults:
  duration: "PT8H"  # Default to 8 hours
  justification: "Requested via az-pim-cli"

# Role aliases
aliases:
  # Azure AD role alias
  global-admin:
    role: "62e90394-69f5-4237-9190-012177145e10"  # Global Administrator role ID
    duration: "PT2H"
    justification: "Emergency administrative access"
    scope: "directory"
  
  # Azure AD role with ticket system
  security-admin:
    role: "Security Administrator"
    duration: "PT4H"
    justification: "Security investigation"
    scope: "directory"
  
  # Subscription-level role
  prod-owner:
    role: "Owner"
    duration: "PT8H"
    justification: "Production environment deployment"
    scope: "subscription"
    subscription: "12345678-1234-1234-1234-123456789abc"
  
  # Resource group role
  dev-contributor:
    role: "Contributor"
    duration: "PT12H"
    justification: "Development work"
    scope: "subscription"
    subscription: "12345678-1234-1234-1234-123456789abc"
  
  # Short-term access
  quick-access:
    role: "Reader"
    duration: "PT1H"
    justification: "Quick review"
    scope: "subscription"
```

## Usage with Aliases

Once configured, you can use aliases to quickly activate roles:

```bash
# Activate using alias
az-pim activate global-admin

# Override alias duration
az-pim activate global-admin --duration 1

# Override alias justification
az-pim activate global-admin --justification "Password reset required"
```

## Finding Role IDs

To find Azure AD role IDs, you can use:

```bash
# Using Azure CLI
az ad sp list --all --query "[?appDisplayName=='Microsoft Graph'].{name:appDisplayName, id:id}" -o table

# Or check Azure Portal
# Azure AD > Roles and administrators > [Select Role] > Copy Object ID
```

## Duration Format

Durations use ISO 8601 format:
- `PT30M` = 30 minutes
- `PT1H` = 1 hour
- `PT2H` = 2 hours
- `PT4H` = 4 hours
- `PT8H` = 8 hours
- `PT12H` = 12 hours

## Scope Options

- `directory` - Azure AD role (default)
- `subscription` - Subscription-level resource role
- `resource` - Resource-specific role (requires full scope path)

## Advanced Configuration

### Using Resource-Specific Scopes

For more specific scopes:

```yaml
aliases:
  keyvault-admin:
    role: "Key Vault Administrator"
    duration: "PT4H"
    justification: "Key management"
    scope: "subscriptions/{sub-id}/resourceGroups/{rg-name}/providers/Microsoft.KeyVault/vaults/{vault-name}"
```

### Multiple Environments

You can maintain separate config files:

```bash
# Development environment
az-pim activate dev-role --config ~/.az-pim-cli/dev-config.yml

# Production environment
az-pim activate prod-role --config ~/.az-pim-cli/prod-config.yml
```
