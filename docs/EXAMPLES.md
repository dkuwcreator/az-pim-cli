# Azure PIM CLI Examples

This document provides practical examples for using the Azure PIM CLI.

## Basic Usage

### List Available Roles

```bash
# List all eligible Azure AD roles
az-pim list

# List eligible resource roles for current subscription
az-pim list --resource

# List roles for specific subscription
az-pim list --resource --scope "subscriptions/12345678-1234-1234-1234-123456789abc"

# Interactive selection mode - list roles and activate
az-pim list --select

# Interactive selection for resource roles
az-pim list --resource --select
```

### Activate Roles

```bash
# Activate Azure AD role with defaults
az-pim activate "Global Administrator"

# Activate with custom duration (4 hours)
az-pim activate "Security Administrator" --duration 4

# Activate with custom justification
az-pim activate "User Administrator" \
  --duration 2 \
  --justification "User account management tasks"

# Activate with ticket information
az-pim activate "Privileged Role Administrator" \
  --duration 4 \
  --justification "PIM configuration update" \
  --ticket "INC123456" \
  --ticket-system "ServiceNow"

# Activate by role number (from list output)
az-pim activate 1 --duration 4 --justification "Quick access"

# Using # prefix with role number
az-pim activate "#3" --duration 2 --justification "Emergency access"
```

### Prompting and Defaults

When running in a TTY, missing required inputs are prompted with sensible defaults:

```bash
# Duration and justification prompt with defaults from config (or 8h/"Requested via az-pim-cli")
az-pim activate "User Administrator"

# Ticket prompts only when partial ticket info is supplied
az-pim activate "Privileged Role Administrator" --ticket INC123456

# Alias missing subscription uses current subscription automatically in non-TTY; prompts in TTY
az-pim activate prod-access --resource --scope "subscriptions/<sub-id>"  # scope still required for resource roles
```

Non-TTY runs will fail fast if required fields are missing (e.g., alias without a role) and will not hang waiting for input. Provide required values via flags in automation.

### Activate Resource Roles

```bash
# Activate subscription Owner role
az-pim activate "8e3af657-a8ff-443c-a75c-2fe8c4bcb635" \
  --resource \
  --scope "subscriptions/12345678-1234-1234-1234-123456789abc" \
  --duration 8 \
  --justification "Production deployment"

# Activate Contributor role for current subscription
az-pim activate "Contributor" --resource --duration 4

# Activate resource role by number
az-pim activate 2 --resource --duration 4 --justification "Quick access"
```

## Alias Management

### Create Aliases

```bash
# Simple Azure AD role alias
az-pim alias add emergency-admin "Global Administrator" \
  --duration "PT2H" \
  --justification "Emergency access"

# Resource role alias with subscription
az-pim alias add prod-access "Owner" \
  --duration "PT8H" \
  --justification "Production deployment" \
  --scope "subscription" \
  --subscription "12345678-1234-1234-1234-123456789abc"

# Development environment alias
az-pim alias add dev-access "Contributor" \
  --duration "PT12H" \
  --justification "Development work" \
  --scope "subscription" \
  --subscription "87654321-4321-4321-4321-210987654321"
```

### Use Aliases

```bash
# Activate using alias
az-pim activate emergency-admin

# Override alias duration
az-pim activate prod-access --duration 4

# Override alias justification
az-pim activate dev-access --justification "Hotfix deployment"
```

### Manage Aliases

```bash
# List all configured aliases
az-pim alias list

# Remove an alias
az-pim alias remove emergency-admin
```

## Approval Workflow

### List and Approve Requests

```bash
# List pending approval requests
az-pim pending

# Approve a request
az-pim approve "12345678-abcd-efgh-ijkl-123456789012" \
  --justification "Approved for scheduled maintenance"
```

## View History

```bash
# View last 30 days of activations
az-pim history

# View last 7 days
az-pim history --days 7

# View last 90 days
az-pim history --days 90
```

## Common Scenarios

### Scenario 1: Emergency Break-Glass Access

```bash
# Create emergency admin alias
az-pim alias add break-glass "Global Administrator" \
  --duration "PT1H" \
  --justification "Emergency break-glass access"

# Use when needed
az-pim activate break-glass --ticket "INC999999" --ticket-system "ServiceNow"
```

### Scenario 2: Scheduled Production Deployment

```bash
# Create production deployment alias
az-pim alias add prod-deploy "Owner" \
  --duration "PT4H" \
  --justification "Production deployment - Change #" \
  --scope "subscription" \
  --subscription "prod-sub-id"

# Activate before deployment
az-pim activate prod-deploy --justification "Production deployment - CHG123456"
```

### Scenario 3: Development Team Access

```bash
# Create dev access for team members
az-pim alias add dev-contributor "Contributor" \
  --duration "PT8H" \
  --justification "Development work" \
  --scope "subscription" \
  --subscription "dev-sub-id"

# Activate at start of workday
az-pim activate dev-contributor
```

### Scenario 4: Security Investigation

```bash
# Create security investigation alias
az-pim alias add security-investigation "Security Administrator" \
  --duration "PT4H" \
  --justification "Security incident investigation"

# Activate for investigation
az-pim activate security-investigation \
  --ticket "SEC-2024-001" \
  --ticket-system "Jira"
```

### Scenario 5: User Management

```bash
# Quick user admin access
az-pim activate "User Administrator" \
  --duration 1 \
  --justification "Password reset for executive team"
```

### Scenario 6: Interactive Role Selection

```bash
# List roles and select interactively
az-pim list --select

# After seeing the list, you'll be prompted to:
# 1. Enter the role number to activate
# 2. Specify duration (default: 8 hours)
# 3. Provide justification

# This is useful when you're not sure of the exact role name
# or want a quick selection workflow
```

### Scenario 7: Quick Activation by Number

```bash
# First, list available roles to see the numbers
az-pim list

# Then activate by number (much faster than typing full role ID)
az-pim activate 1 --duration 4 --justification "Quick access needed"

# Works with resource roles too
az-pim list --resource
az-pim activate "#2" --resource --duration 2 --justification "Emergency access"
```

## Automation Examples

### Shell Script for Daily Access

```bash
#!/bin/bash
# activate-daily-access.sh

echo "Activating daily development access..."
az-pim activate dev-access

echo "Activating monitoring access..."
az-pim activate monitoring-reader

echo "Access activated for 8 hours"
```

### Python Script for Conditional Activation

```python
#!/usr/bin/env python3
import subprocess
import sys
from datetime import datetime

def activate_role(role_alias, duration=8, justification=""):
    """Activate a PIM role using alias."""
    cmd = [
        "az-pim", "activate", role_alias,
        "--duration", str(duration),
        "--justification", justification
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0

# Check if it's a weekday
if datetime.now().weekday() < 5:  # Monday = 0, Friday = 4
    print("Weekday detected, activating work roles...")
    activate_role("dev-access", duration=8, justification="Daily development work")
else:
    print("Weekend - no automatic activation")
```

## Integration with CI/CD

### GitHub Actions

```yaml
- name: Activate Azure PIM Role
  run: |
    az-pim activate deployment-admin \
      --justification "GitHub Actions deployment - ${{ github.run_id }}"
```

### Azure DevOps Pipeline

```yaml
- script: |
    az-pim activate deployment-admin \
      --justification "Azure Pipeline deployment - $(Build.BuildNumber)"
  displayName: 'Activate PIM Role'
```

## Tips and Best Practices

1. **Use Short Durations**: Request the minimum time needed
2. **Provide Specific Justifications**: Include ticket numbers and specific reasons
3. **Create Role-Specific Aliases**: One alias per common use case
4. **Review History Regularly**: Check activation patterns with `az-pim history`
5. **Automate Common Activations**: Use scripts for daily/regular access patterns
6. **Document Team Aliases**: Share alias configurations with team members
7. **Use Interactive Mode**: When unsure of role names, use `az-pim list --select` for guided selection
8. **Activate by Number**: Use role numbers (e.g., `az-pim activate 1`) for faster activation after listing roles
9. **Combine List and Activate**: Run `az-pim list` first to see all roles with numbers, then activate by number
