# CLI Output Comparison: Before and After

## Command Help - New Flags Added

### az-pim list --help

**AFTER (New Features):**
```
Usage: az-pim list [OPTIONS]

 List eligible roles.

╭─ Options ────────────────────────────────────────────────────────────────╮
│ --resource    -r               List resource roles instead of directory  │
│ --scope       -s      TEXT     Scope for resource roles                  │
│ --full-scope                   Show full scope paths (NEW)               │
│ --limit       -l      INTEGER  Limit number of results (NEW)             │
│ --verbose     -v               Enable verbose output (NEW)               │
│ --help                         Show this message and exit.               │
╰──────────────────────────────────────────────────────────────────────────╯
```

**BEFORE:**
```
Usage: az-pim list [OPTIONS]

 List eligible roles.

╭─ Options ────────────────────────────────────────────────────────────────╮
│ --resource    -r               List resource roles instead of directory  │
│ --scope       -s      TEXT     Scope for resource roles                  │
│ --help                         Show this message and exit.               │
╰──────────────────────────────────────────────────────────────────────────╯
```

## Error Messages - More Informative

### Authentication Error

**AFTER:**
```
Authentication Error: Not logged in to Azure CLI
Suggestion: Run 'az login' to authenticate with Azure
```

**BEFORE:**
```
Error: ...subprocess.CalledProcessError...
```

### Network Error with DNS Issues

**AFTER:**
```
Network Error: Connection error during list role assignments: [Errno -2] Name or service not known
Endpoint: https://management.azure.com/...
💡 Tip: If you're experiencing DNS issues, try enabling IPv4-only mode:
   export AZ_PIM_IPV4_ONLY=1
```

**BEFORE:**
```
Error: ConnectionError: ...
```

### Permission Error

**AFTER:**
```
Permission Error: Permission denied for list role assignments. Principal ID: abc123...
Endpoint: https://management.azure.com/...
Required permissions: RoleManagement.ReadWrite.Directory or equivalent Azure RBAC permissions
```

**BEFORE:**
```
Error: 403 Client Error: Forbidden
```

## Role Listing Output

### Default Output with Scope Column

**AFTER (with new scope column):**
```
Eligible Azure AD Roles
Backend: ARM | IPv4-only: off
Found 3 role(s)

┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Role Name          ┃ Role ID       ┃ Status ┃ Scope              ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ Contributor        │ /providers... │ Active │ sub:12345678...    │
│ Reader             │ /providers... │ Active │ sub:12345678.../   │
│                    │               │        │ rg:my-rg           │
│ Global Admin       │ abc-def-123   │ Active │ /                  │
└────────────────────┴───────────────┴────────┴────────────────────┘
```

**BEFORE:**
```
Eligible Azure AD Roles

┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Role Name          ┃ Role ID       ┃ Status ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ Contributor        │ /providers... │ Active │
│ Reader             │ /providers... │ Active │
│ Global Admin       │ abc-def-123   │ Active │
└────────────────────┴───────────────┴────────┘
```

## Verbose Mode Output

**NEW FEATURE - Verbose Mode:**
```bash
$ az-pim list --verbose

[DEBUG] PIM Client initialized with backend: ARM
[DEBUG] IPv4-only mode: False
Fetching eligible roles...
[DEBUG] GET https://management.azure.com/providers/Microsoft.Authorization/roleEligibilityScheduleInstances
[DEBUG] Params: {'api-version': '2020-10-01', '$filter': 'asTarget()'}
[DEBUG] Response status: 200
[DEBUG] Retrieved 3 roles (total: 3)

Eligible Azure AD Roles
Backend: ARM | IPv4-only: off
Found 3 role(s)
...
```

## Environment Variable Configuration

**NEW FEATURE - Environment Variables:**

```bash
# Enable IPv4-only mode for DNS issues
export AZ_PIM_IPV4_ONLY=1

# Choose backend (ARM is default and recommended)
export AZ_PIM_BACKEND=ARM

# Use with CLI
az-pim list --verbose
```

Output shows:
```
[DEBUG] PIM Client initialized with backend: ARM
[DEBUG] IPv4-only mode: True
Backend: ARM | IPv4-only: 1
```

## Pagination and Limiting

**NEW FEATURE - Limit Results:**

```bash
# Get only first 5 roles for quick preview
$ az-pim list --limit 5

Eligible Azure AD Roles
Found 5 role(s)

┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Role Name          ┃ Role ID       ┃ Status ┃ Scope              ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ ... (5 roles) ...
└────────────────────┴───────────────┴────────┴────────────────────┘
```

**NEW FEATURE - Automatic Pagination:**

Previously: Only first page of results returned
Now: Automatically fetches all pages (can be limited with --limit)

## Full Scope Display

**NEW FEATURE - Full Scope Paths:**

```bash
$ az-pim list --full-scope

┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Role Name          ┃ Role ID       ┃ Status ┃ Scope                              ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Contributor        │ /providers... │ Active │ /subscriptions/12345678-1234-...   │
│                    │               │        │ 1234-1234-123456789abc             │
└────────────────────┴───────────────┴────────┴────────────────────────────────────┘
```

## Summary of UI Improvements

1. ✅ Three new CLI flags: --verbose, --limit, --full-scope
2. ✅ New scope column in role listings
3. ✅ Informative error messages with actionable suggestions
4. ✅ Verbose mode shows debug information and backend status
5. ✅ Environment variable support for configuration
6. ✅ Pagination automatically handles large role sets
7. ✅ No breaking changes - all existing commands work as before
