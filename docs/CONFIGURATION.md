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
  
  # Smart input resolution settings
  fuzzy_matching: true           # Enable fuzzy name matching
  fuzzy_threshold: 0.8           # Minimum similarity score (0.0-1.0)
  cache_ttl_seconds: 300         # Cache eligible roles for 5 minutes

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

## Prompting Behavior

- Interactivity is implied by TTY: when running in a terminal, missing required inputs (duration, justification, scope, ticket pair) prompt with defaults sourced from this config or the current subscription.
- In non-TTY/automation, missing required inputs fail fast instead of prompting. Provide required values via flags or update the config/alias.
- Ticket info is only sent when both `ticket` and `ticket-system` are supplied; incomplete pairs are ignored in non-TTY and prompted to complete in TTY.

## Advanced Configuration

### Smart Input Resolution

The CLI now supports intelligent input matching for roles and scopes, making it easier to activate roles without exact names:

#### Matching Strategies (in priority order)

1. **Exact Match**: Exact string match (fastest)
   ```bash
   az-pim activate "Security Administrator"
   ```

2. **Case-Insensitive Match**: Ignores case differences
   ```bash
   az-pim activate "security administrator"  # Matches "Security Administrator"
   ```

3. **Prefix Match**: Matches beginning of name
   ```bash
   az-pim activate "Security"  # Matches "Security Administrator" or "Security Reader"
   ```

4. **Fuzzy Match**: Handles typos and partial matches
   ```bash
   az-pim activate "Sec Admin"  # Matches "Security Administrator"
   az-pim activate "Contributer"  # Matches "Contributor" (fixes typo)
   ```

#### Configuration Options

```yaml
defaults:
  # Enable/disable fuzzy matching
  fuzzy_matching: true
  
  # Minimum similarity score for fuzzy matches (0.0 = any match, 1.0 = exact only)
  fuzzy_threshold: 0.8
  
  # Cache results to reduce API calls (in seconds)
  cache_ttl_seconds: 300
```

#### Interactive vs Non-Interactive Mode

**Interactive (TTY):**
- Multiple matches: Shows numbered list for selection
- No matches: Shows "Did you mean?" suggestions
- User-friendly error messages with tips

**Non-Interactive (Scripts/Automation):**
- Single match: Uses it silently
- Multiple matches: Fails with error listing all candidates
- No matches: Fails with suggestions for troubleshooting

#### Enhanced Fuzzy Matching (Optional)

For better performance with large role sets, install the optional fuzzy matching library:

```bash
pip install az-pim-cli[fuzzy]
```

This installs `rapidfuzz` for faster and more accurate fuzzy matching. The CLI automatically uses it if available, otherwise falls back to Python's built-in `difflib`.

#### Examples

```bash
# Exact match (no ambiguity)
az-pim activate Owner

# Partial name (unique prefix)
az-pim activate Sec  # If only one role starts with "Sec"

# Typo correction
az-pim activate Contribtor  # Fuzzy matches "Contributor"

# Interactive selection with multiple matches
az-pim activate Security
# Shows:
# 1. Security Administrator
# 2. Security Reader
# Select number: _

# Scope matching (subscription or resource group names)
az-pim activate Owner --scope "Production"  # Matches subscription/RG named "Production"
az-pim activate Owner --scope "prod"  # Matches "Production-Subscription" via prefix
```

#### Disabling Fuzzy Matching

If you prefer exact matching only (for scripts), disable fuzzy matching:

```yaml
defaults:
  fuzzy_matching: false
```

Or use exact role IDs/full paths to bypass matching entirely:

```bash
# Use full role definition ID
az-pim activate "/providers/Microsoft.Authorization/roleDefinitions/8e3af657-a8ff-443c-a75c-2fe8c4bcb635"

# Use full scope path
az-pim activate Owner --scope "/subscriptions/12345678-1234-1234-1234-123456789abc"
```

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
