# Example Output Scenarios

This document shows what users will see when using the smart input resolution features.

## Scenario 1: Exact Match (Silent Success)

```bash
$ az-pim activate "Owner" --duration 4 --justification "Deployment"

Activating role: Owner
Duration: PT4H
Justification: Deployment

✓ Role activation requested successfully!
Request ID: 12345678-abcd-efgh-ijkl-123456789012
```

## Scenario 2: Case-Insensitive Match (Shows Match Type)

```bash
$ az-pim activate "owner" --duration 4 --justification "Deployment"

Using role 'Owner' (case-insensitive match)

Activating role: Owner
Duration: PT4H
Justification: Deployment

✓ Role activation requested successfully!
Request ID: 12345678-abcd-efgh-ijkl-123456789012
```

## Scenario 3: Prefix Match (Shows Match Type)

```bash
$ az-pim activate "Sec Admin" --duration 2 --justification "Review"

Using role 'Security Administrator' (prefix match)

Activating role: Security Administrator
Duration: PT2H
Justification: Review

✓ Role activation requested successfully!
Request ID: 12345678-abcd-efgh-ijkl-123456789012
```

## Scenario 4: Fuzzy Match with Typo (Shows Match + Score)

```bash
$ az-pim activate "Contributer" --duration 4 --justification "Code review"

Using role 'Contributor' (fuzzy match: 91%)

Activating role: Contributor
Duration: PT4H
Justification: Code review

✓ Role activation requested successfully!
Request ID: 12345678-abcd-efgh-ijkl-123456789012
```

## Scenario 5: Multiple Matches - Interactive (TTY)

```bash
$ az-pim activate "Security"

Multiple roles match your input:
  1. Security Administrator
  2. Security Reader

Select number [1]: 2

Activating role: Security Reader
Duration: PT8H
Justification: Requested via az-pim-cli

✓ Role activation requested successfully!
Request ID: 12345678-abcd-efgh-ijkl-123456789012
```

## Scenario 6: Multiple Matches - Non-Interactive (Script)

```bash
$ az-pim activate "Security" --duration 4 --justification "Review"

✗ Multiple roles match 'Security' (non-interactive mode)

Matching candidates:
  • Security Administrator
  • Security Reader

Tip: Use exact name/ID or run in interactive mode
```

## Scenario 7: No Match with Suggestions

```bash
$ az-pim activate "Admin" --duration 4 --justification "Work"

✗ Role 'Admin' not found

Did you mean:
  1. Global Administrator
  2. Privileged Role Administrator
  3. User Administrator

Tip: Run 'az-pim list' to see all available roles
```

## Scenario 8: No Match, No Good Suggestions

```bash
$ az-pim activate "XYZ123" --duration 4 --justification "Work"

✗ Role 'XYZ123' not found

Did you mean:
  1. Owner
  2. Contributor
  3. Reader

Tip: Run 'az-pim list' to see all available roles
```

## Scenario 9: Scope Name Matching

```bash
$ az-pim activate "Owner" --resource --scope "prod" --duration 4

Using scope 'Production-Subscription' (prefix match)

Activating role: Owner
Duration: PT4H
Justification: Requested via az-pim-cli
Scope: /subscriptions/12345678-1234-1234-1234-123456789abc

✓ Role activation requested successfully!
Request ID: 12345678-abcd-efgh-ijkl-123456789012
```

## Scenario 10: Interactive Selection Cancelled

```bash
$ az-pim activate "Security"

Multiple roles match your input:
  1. Security Administrator
  2. Security Reader

Select number [1]: ^C

Selection cancelled
```

## Scenario 11: Invalid Role Number

```bash
$ az-pim activate "999" --duration 4 --justification "Work"

Looking up role #999 from recent list...

✗ Invalid role number 999 (must be 1-10)
```

## Scenario 12: Role by Number (from list)

```bash
$ az-pim list

Eligible Roles
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┓
┃ #  ┃ Role                 ┃ Type   ┃ Expires ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━┩
│ 1  │ Global Administrator │ Direct │ -       │
│ 2  │ Security Admin       │ Direct │ -       │
└────┴──────────────────────┴────────┴─────────┘

$ az-pim activate 2 --duration 2 --justification "Security review"

Selected: Security Administrator

Activating role: Security Administrator
Duration: PT2H
Justification: Security review

✓ Role activation requested successfully!
Request ID: 12345678-abcd-efgh-ijkl-123456789012
```

## Scenario 13: Fuzzy Disabled (Config)

```yaml
# ~/.az-pim-cli/config.yml
defaults:
  fuzzy_matching: false
```

```bash
$ az-pim activate "Contributer" --duration 4 --justification "Work"

✗ Role 'Contributer' not found

Did you mean:
  1. Contributor
  2. Reader
  3. Owner

Tip: Run 'az-pim list' to see all available roles
```

## Scenario 14: Caching in Action

```bash
# First activation (fetches roles from API)
$ az-pim activate "Owner" --resource --duration 2 --justification "Deploy"
Fetching eligible roles...  # <-- API call
✓ Role activation requested successfully!

# Second activation within 5 minutes (uses cache)
$ az-pim activate "Contributor" --resource --duration 2 --justification "Deploy"
# (no "Fetching..." message, uses cached data)
✓ Role activation requested successfully!
```

## Scenario 15: Empty Input

```bash
$ az-pim activate "" --duration 4 --justification "Work"

✗ Role input is required
```

## Scenario 16: With rapidfuzz Installed

```bash
$ pip install az-pim-cli[fuzzy]
$ az-pim activate "Sec Admnistrator" --duration 2 --justification "Review"

Using role 'Security Administrator' (fuzzy match: 87%)
# (matches faster with rapidfuzz than with difflib)

✓ Role activation requested successfully!
```

## Notes

- **TTY Detection**: System automatically detects if running in a terminal vs script
- **Match Strategy**: Shows which strategy was used (except exact matches)
- **Scores**: Fuzzy matches show percentage similarity
- **Suggestions**: Always shows top 3 suggestions when no match found
- **Performance**: Cached results make subsequent activations faster
- **Colors**: Actual output includes colors via Rich library (green for success, red for errors, yellow for warnings)
