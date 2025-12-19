# Examples

This guide provides practical examples for using Azure PIM CLI v2.0 with the three focused commands:
- `azp-res` (Azure resources)
- `azp-entra` (Entra directory roles)
- `azp-groups` (Entra group memberships)

## Table of Contents

- [Azure Resources (`azp-res`)](#azure-resources-azp-res)
- [Entra Directory Roles (`azp-entra`)](#entra-directory-roles-azp-entra)
- [Entra Group Memberships (`azp-groups`)](#entra-group-memberships-azp-groups)
- [Verbose Logging](#verbose-logging)
- [Common Scenarios](#common-scenarios)

## Azure Resources (`azp-res`)

### List Eligible Resource Roles

```bash
# List roles for current subscription
azp-res list

# List roles for specific subscription
azp-res list --scope "subscriptions/12345678-1234-1234-1234-123456789abc"

# List roles for resource group
azp-res list --scope "subscriptions/{sub-id}/resourceGroups/my-rg"

# Limit results
azp-res list --limit 10

# Show full scope paths
azp-res list --full-scope
```

### Activate Resource Roles

```bash
# Activate with role ID
azp-res activate "/subscriptions/{sub-id}/providers/Microsoft.Authorization/roleDefinitions/{role-id}"

# With custom duration and justification
azp-res activate "{role-id}" \
  --duration 4 \
  --justification "Production deployment"

# With specific scope
azp-res activate "{role-id}" \
  --scope "subscriptions/{sub-id}/resourceGroups/my-rg" \
  --duration 2

# With ticket information
azp-res activate "{role-id}" \
  --duration 4 \
  --ticket "INC123456" \
  --ticket-system "ServiceNow"
```

### Resource Role Scenarios

**Scenario 1: Emergency production access**
```bash
# Quick 2-hour access
azp-res activate "{owner-role-id}" \
  --duration 2 \
  --justification "Emergency: Production incident INC-123"
```

**Scenario 2: Planned maintenance window**
```bash
# 4-hour access for maintenance
azp-res activate "{contributor-role-id}" \
  --duration 4 \
  --justification "Planned maintenance window" \
  --ticket "CHG0012345" \
  --ticket-system "ServiceNow"
```

**Scenario 3: Resource group specific access**
```bash
# Access to specific resource group only
azp-res activate "{role-id}" \
  --scope "subscriptions/{sub-id}/resourceGroups/prod-rg" \
  --duration 8 \
  --justification "Application deployment"
```

## Entra Directory Roles (`azp-entra`)

### List Eligible Entra Roles

```bash
# List all eligible Entra directory roles
azp-entra list

# Limit results
azp-entra list --limit 5
```

### Activate Entra Roles

```bash
# Activate an Entra role
azp-entra activate "{role-id}"

# With custom duration and justification
azp-entra activate "{role-id}" \
  --duration 2 \
  --justification "Emergency password reset"

# With ticket information
azp-entra activate "{role-id}" \
  --duration 1 \
  --ticket "INC999999" \
  --ticket-system "ServiceNow"
```

### View Activation History

```bash
# View last 30 days (default)
azp-entra history

# View last 7 days
azp-entra history --days 7

# View last 90 days
azp-entra history --days 90
```

### Approval Workflow

```bash
# List pending approval requests
azp-entra pending

# Approve a specific request
azp-entra approve {request-id} \
  --justification "Approved for scheduled maintenance"
```

### Entra Role Scenarios

**Scenario 1: Emergency Global Admin access**
```bash
# 1-hour emergency access
azp-entra activate "{global-admin-role-id}" \
  --duration 1 \
  --justification "Emergency: Account lockout recovery"
```

**Scenario 2: User administration**
```bash
# 4-hour access for user management tasks
azp-entra activate "{user-admin-role-id}" \
  --duration 4 \
  --justification "Quarterly user access review"
```

**Scenario 3: Security operations**
```bash
# 8-hour access for security investigation
azp-entra activate "{security-admin-role-id}" \
  --duration 8 \
  --justification "Security incident investigation" \
  --ticket "SEC-2024-001" \
  --ticket-system "Jira"
```

## Entra Group Memberships (`azp-groups`)

### List Eligible Group Assignments

```bash
# List all eligible group assignments
azp-groups list

# Limit results
azp-groups list --limit 10
```

### Activate Group Memberships

```bash
# Activate as member (default)
azp-groups activate "{group-id}"

# Activate as member with custom settings
azp-groups activate "{group-id}" \
  --access member \
  --duration 8 \
  --justification "Daily operations"

# Activate as owner
azp-groups activate "{group-id}" \
  --access owner \
  --duration 4 \
  --justification "Group management tasks"

# With ticket information
azp-groups activate "{group-id}" \
  --access member \
  --duration 2 \
  --ticket "REQ456" \
  --ticket-system "ServiceNow"
```

### View Group Activation History

```bash
# View last 30 days (default)
azp-groups history

# View last 7 days
azp-groups history --days 7
```

### Group Membership Scenarios

**Scenario 1: Security operations team**
```bash
# Join security operations group for shift
azp-groups activate "{security-ops-group-id}" \
  --access member \
  --duration 8 \
  --justification "Security operations shift"
```

**Scenario 2: Temporary group ownership**
```bash
# Become group owner for management tasks
azp-groups activate "{team-group-id}" \
  --access owner \
  --duration 2 \
  --justification "Group membership review"
```

**Scenario 3: Application support group**
```bash
# Join application support group
azp-groups activate "{app-support-group-id}" \
  --access member \
  --duration 4 \
  --justification "Application troubleshooting" \
  --ticket "INC789" \
  --ticket-system "Jira"
```

## Verbose Logging

Enable verbose logging for any command to see detailed information:

```bash
# Verbose resource listing
azp-res list --verbose

# Verbose Entra role activation
azp-entra activate "{role-id}" --verbose \
  --duration 2 \
  --justification "Test"

# Verbose group listing
azp-groups list --verbose
```

Verbose output includes:
- Command name
- OAuth scope (ARM or Graph)
- Backend hint
- IPv4-only mode status
- API calls and responses
- Detailed error traces

## Common Scenarios

### Scenario 1: Multi-Tier Application Deployment

```bash
# Step 1: Activate resource role for infrastructure
azp-res activate "{contributor-role-id}" \
  --scope "subscriptions/{sub-id}/resourceGroups/app-rg" \
  --duration 4 \
  --justification "Application deployment - infrastructure"

# Step 2: Activate Entra role for app registration
azp-entra activate "{app-admin-role-id}" \
  --duration 2 \
  --justification "Application deployment - app registration"

# Step 3: Join deployment team group
azp-groups activate "{deploy-team-group-id}" \
  --access member \
  --duration 4 \
  --justification "Application deployment"
```

### Scenario 2: Security Incident Response

```bash
# Activate multiple roles for comprehensive access

# 1. Activate Security Administrator
azp-entra activate "{security-admin-role-id}" \
  --duration 4 \
  --justification "Security incident response" \
  --ticket "SEC-2024-042"

# 2. Activate resource access for audit logs
azp-res activate "{reader-role-id}" \
  --duration 4 \
  --justification "Security incident investigation"

# 3. Join security operations group
azp-groups activate "{security-ops-group-id}" \
  --access member \
  --duration 4 \
  --justification "Security incident response"
```

### Scenario 3: Scheduled Maintenance Window

```bash
# 8-hour maintenance window

# Activate resource Owner role
azp-res activate "{owner-role-id}" \
  --scope "subscriptions/{sub-id}" \
  --duration 8 \
  --justification "Scheduled maintenance window" \
  --ticket "CHG0054321" \
  --ticket-system "ServiceNow"

# View activation history to confirm
azp-res history  # Note: Resource history not yet implemented, use Azure Portal
```

### Scenario 4: Cross-Environment Access

```bash
# Development environment (longer duration)
azp-res activate "{contributor-role-id}" \
  --scope "subscriptions/{dev-sub-id}" \
  --duration 8 \
  --justification "Development work"

# Production environment (shorter duration)
azp-res activate "{contributor-role-id}" \
  --scope "subscriptions/{prod-sub-id}" \
  --duration 2 \
  --justification "Production hotfix deployment" \
  --ticket "INC-PROD-123"
```

### Scenario 5: Approval Workflow for Team

```bash
# As approver: Check pending requests
azp-entra pending

# Approve team member's request
azp-entra approve {request-id} \
  --justification "Approved - Verified with manager"

# As requester: Check history to confirm activation
azp-entra history --days 1
```

## Using Aliases

Configure aliases in `~/.az-pim-cli/config.yml`:

```yaml
aliases:
  res:prod:
    role: "Owner"
    duration: "PT4H"
    justification: "Production access"
    scope: "subscriptions/{prod-sub-id}"
  
  entra:emergency:
    role: "Global Administrator"
    duration: "PT1H"
    justification: "Emergency access"
  
  groups:oncall:
    group_id: "{oncall-group-id}"
    access: "member"
    duration: "PT12H"
    justification: "On-call rotation"
```

Then activate using aliases:

```bash
# Use resource alias
azp-res activate prod

# Use Entra role alias
azp-entra activate emergency

# Use group alias
azp-groups activate oncall
```

## Troubleshooting Examples

### DNS Resolution Issues

```bash
# Enable IPv4-only mode
export AZ_PIM_IPV4_ONLY=1

# Then retry the command
azp-res list
```

### Check Version

```bash
# Check command versions
azp-res version
azp-entra version
azp-groups version
```

### Detailed Error Traces

```bash
# Use verbose mode for troubleshooting
azp-res list --verbose
azp-entra activate "{role-id}" --verbose
```

## Tips and Best Practices

1. **Use short durations**: Request only the time you need
2. **Include justifications**: Make activations auditable
3. **Use ticket systems**: Link to change/incident tickets when available
4. **Configure aliases**: Save commonly used roles as aliases
5. **Check history**: Review past activations for audit purposes
6. **Verbose logging**: Use `--verbose` when troubleshooting
7. **Limit results**: Use `--limit` when testing or exploring roles
