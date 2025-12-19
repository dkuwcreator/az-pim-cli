# Configuration Guide

Azure PIM CLI v2.0 uses a YAML configuration file located at `~/.az-pim-cli/config.yml`.

## Configuration File Structure

```yaml
aliases:
  # Resource role aliases (prefix with 'res:')
  res:prod-owner:
    role: "/subscriptions/{sub-id}/providers/Microsoft.Authorization/roleDefinitions/{role-id}"
    duration: "PT4H"
    justification: "Production environment access"
    scope: "subscriptions/{subscription-id}"
  
  # Entra role aliases (prefix with 'entra:')
  entra:emergency:
    role: "Global Administrator"
    duration: "PT2H"
    justification: "Emergency access"
    scope: "directory"
  
  entra:security-admin:
    role: "Security Administrator"
    duration: "PT8H"
    justification: "Security operations"
  
  # Group aliases (prefix with 'groups:')
  groups:security-team:
    group_id: "{group-id}"
    access: "member"  # or "owner"
    duration: "PT8H"
    justification: "Security operations"

defaults:
  duration: "PT8H"
  justification: "Requested via az-pim-cli"
```

## Alias Prefixes

In v2.0, aliases use prefixes to identify which command they belong to:

- **`res:`** - For Azure resource roles (used with `azp-res`)
- **`entra:`** - For Entra directory roles (used with `azp-entra`)
- **`groups:`** - For Entra group memberships (used with `azp-groups`)

## Alias Configuration Fields

### Resource Role Aliases (`res:`)

```yaml
res:my-alias:
  role: "Role ID or name"                    # Required
  duration: "PT8H"                           # Optional (default: PT8H)
  justification: "Justification text"        # Optional
  scope: "subscriptions/{sub-id}"            # Optional (default: current subscription)
```

### Entra Role Aliases (`entra:`)

```yaml
entra:my-alias:
  role: "Role ID or name"                    # Required
  duration: "PT8H"                           # Optional (default: PT8H)
  justification: "Justification text"        # Optional
  scope: "directory"                         # Optional (default: "directory")
```

### Group Aliases (`groups:`)

```yaml
groups:my-alias:
  group_id: "{group-id}"                     # Required
  access: "member"                           # Optional: "member" or "owner" (default: member)
  duration: "PT8H"                           # Optional (default: PT8H)
  justification: "Justification text"        # Optional
```

## Environment Variables

### AZ_PIM_IPV4_ONLY

Force IPv4-only DNS resolution to work around IPv6 connectivity issues.

```bash
export AZ_PIM_IPV4_ONLY=1
```

**Accepted values**: `1`, `true`, `yes` (case-insensitive)

### Verbose Logging

Use the `--verbose` flag on any command to enable detailed logging:

```bash
azp-res list --verbose
azp-entra activate "{role-id}" --verbose
azp-groups list --verbose
```

Verbose output includes:
- Command name
- OAuth scope (ARM or Graph)
- Backend hint
- IPv4-only mode status
- Detailed error traces

## Duration Format

Durations use ISO 8601 format:

- `PT1H` = 1 hour
- `PT2H` = 2 hours
- `PT4H` = 4 hours
- `PT8H` = 8 hours (default)
- `PT30M` = 30 minutes

You can also use the `--duration` flag with hours as a number:
- `--duration 1` = 1 hour
- `--duration 4` = 4 hours
- `--duration 8` = 8 hours

## Using Aliases

Once configured, you can use aliases without the prefix:

```bash
# Use resource alias (defined as 'res:prod-owner')
azp-res activate prod-owner

# Use Entra role alias (defined as 'entra:emergency')
azp-entra activate emergency

# Use group alias (defined as 'groups:security-team')
azp-groups activate security-team
```

## Configuration File Location

Default location: `~/.az-pim-cli/config.yml`

The configuration file is created automatically on first run with example aliases.

## Examples

### Example 1: Production Access

```yaml
res:prod-owner:
  role: "Owner"
  duration: "PT4H"
  justification: "Production deployment"
  scope: "subscriptions/12345678-1234-1234-1234-123456789abc"
```

Usage:
```bash
azp-res activate prod-owner
```

### Example 2: Emergency Entra Access

```yaml
entra:emergency:
  role: "Global Administrator"
  duration: "PT1H"
  justification: "Emergency incident response"
```

Usage:
```bash
azp-entra activate emergency
```

### Example 3: Security Group Access

```yaml
groups:sec-ops:
  group_id: "12345678-1234-1234-1234-123456789abc"
  access: "member"
  duration: "PT8H"
  justification: "Security operations shift"
```

Usage:
```bash
azp-groups activate sec-ops
```

## Best Practices

1. **Use descriptive alias names**: Make it clear what the alias is for
2. **Include justifications**: Pre-fill common justifications to save time
3. **Set appropriate durations**: Match durations to typical usage patterns
4. **Document your aliases**: Add comments in the YAML file
5. **Use prefixes consistently**: Always include the appropriate prefix

## Troubleshooting

### Configuration File Not Found

If the configuration file doesn't exist, it will be created automatically with example aliases when you run any command.

### Invalid YAML Syntax

If you see YAML parsing errors, check:
- Indentation (use spaces, not tabs)
- Quotes around strings with special characters
- Proper YAML structure

### Alias Not Found

If an alias isn't recognized:
- Check that you're using the correct command (`azp-res`, `azp-entra`, or `azp-groups`)
- Verify the alias name doesn't include the prefix when using it
- Ensure the alias is defined in the correct section

### Permission Issues

If you get permission errors reading/writing the config file:
- Check file permissions: `chmod 600 ~/.az-pim-cli/config.yml`
- Ensure the directory exists: `mkdir -p ~/.az-pim-cli`
