# Smart Input Resolution Quick Reference

## TL;DR

You can now use partial names, typos, or case-insensitive inputs when activating roles:

```bash
# Before: Required exact name
az-pim activate "Security Administrator"

# Now: Any of these work
az-pim activate "security administrator"  # Case-insensitive
az-pim activate "Security"               # Prefix match (if unique)
az-pim activate "Sec Admin"              # Fuzzy match
az-pim activate "Sec Admnistrator"       # Handles typos
```

## Quick Examples

### Role Matching

```bash
# Exact (fastest)
az-pim activate "Owner"

# Case-insensitive
az-pim activate "OWNER"

# Prefix (unique)
az-pim activate "Own"

# Fuzzy (typo)
az-pim activate "Ownar"
```

### Scope Matching

```bash
# By name
az-pim activate "Owner" --resource --scope "Production"

# Prefix
az-pim activate "Owner" --resource --scope "prod"

# Case-insensitive
az-pim activate "Owner" --resource --scope "PRODUCTION"
```

### Multiple Matches (Interactive)

```bash
$ az-pim activate "Security"

Multiple roles match your input:
  1. Security Administrator
  2. Security Reader
Select number [1]: 1
```

### Multiple Matches (Scripts)

```bash
$ az-pim activate "Security"  # Non-interactive

✗ Multiple roles match 'Security' (non-interactive mode)
Matching candidates:
  • Security Administrator
  • Security Reader
Tip: Use exact name/ID or run in interactive mode
```

## Configuration

Edit `~/.az-pim-cli/config.yml`:

```yaml
defaults:
  # Enable/disable fuzzy matching
  fuzzy_matching: true
  
  # Minimum similarity (0.0 = any, 1.0 = exact)
  fuzzy_threshold: 0.8
  
  # Cache duration in seconds
  cache_ttl_seconds: 300
```

## Optional Enhanced Fuzzy Matching

Install for better performance:

```bash
pip install az-pim-cli[fuzzy]
```

## Disable Fuzzy Matching (Scripts)

```yaml
# ~/.az-pim-cli/config.yml
defaults:
  fuzzy_matching: false
```

Or use exact IDs:

```bash
az-pim activate "8e3af657-a8ff-443c-a75c-2fe8c4bcb635"
```

## Matching Priority

1. **Exact** → `"Owner"` matches `"Owner"`
2. **Case-insensitive** → `"owner"` matches `"Owner"`
3. **Prefix** → `"Own"` matches `"Owner"`
4. **Fuzzy** → `"Ownar"` matches `"Owner"`

## Tips

- **Scripts**: Use exact IDs or disable fuzzy for deterministic behavior
- **Interactive**: Partial names work great, multiple matches prompt for selection
- **Performance**: Results cached for 5 minutes by default
- **Typos**: Fuzzy matching handles most common typos automatically

## See Also

- [Full Examples](docs/EXAMPLES.md#smart-input-resolution)
- [Configuration Guide](docs/CONFIGURATION.md#smart-input-resolution)
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md)
