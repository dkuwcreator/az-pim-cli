# Migration Guide

## Overview

This guide helps developers migrate to the new architecture introduced in the maintainability upgrade.

## For End Users

**No changes required!** All CLI commands work exactly as before:

```bash
az-pim list
az-pim activate "Global Administrator"
az-pim alias add prod "Owner"
```

Configuration files remain compatible.

## For Developers

### Tooling Changes

#### Linting & Formatting

**Before:**
```bash
black src/
isort src/
flake8 src/
```

**After:**
```bash
ruff format src/        # Replaces black
ruff check --fix src/   # Replaces flake8 + isort
```

**Benefits:**
- 10-100x faster
- Single command
- Auto-fixes most issues

#### Pre-commit Hooks

The pre-commit configuration now uses ruff:

```bash
pre-commit run --all-files
```

### Import Changes

#### Configuration

**Old (still works):**
```python
from az_pim_cli.config import Config

config = Config()
```

**New (recommended):**
```python
from az_pim_cli.infra.config_adapter import EnhancedConfig

config = EnhancedConfig()
```

**Benefits:**
- Pydantic validation
- Environment variable support
- Better error messages

#### Models

**Old (still works):**
```python
from az_pim_cli.models import NormalizedRole, RoleSource
```

**New (recommended):**
```python
from az_pim_cli.domain.models import NormalizedRole, RoleSource
```

**Benefits:**
- Pure domain logic
- No external dependencies
- Easier to test

#### Exceptions

**Old (still works):**
```python
from az_pim_cli.exceptions import PIMError, NetworkError
```

**New (recommended):**
```python
from az_pim_cli.domain.exceptions import PIMError, NetworkError
```

### New Capabilities

#### HTTP Client with Retry

**Example:**
```python
from az_pim_cli.infra.http_client_adapter import HTTPXAdapter

client = HTTPXAdapter(
    timeout=30.0,
    max_retries=3,
    verbose=False,
    ipv4_only=False,
)

# Automatic retry on transient errors
response = client.get("https://api.example.com/data")
```

**Features:**
- Automatic retry with exponential backoff
- Enhanced error messages
- IPv4-only mode for DNS issues

#### Enhanced Configuration

**Example:**
```python
from az_pim_cli.infra.config_adapter import EnhancedConfig, AliasConfig

config = EnhancedConfig()

# Add alias with validation
config.add_alias(
    name="prod",
    role="Contributor",
    duration="4",  # Auto-converts to "PT4H"
    scope="subscription",
)

# Access settings with defaults
fuzzy_enabled = config.get_default("fuzzy_matching", True)
```

**Features:**
- Pydantic validation
- Duration format auto-conversion
- Type-safe accessors

### Testing Changes

#### New Test Structure

Tests now cover adapter layers:

```
tests/
├── test_config.py           # Legacy config tests
├── test_config_adapter.py   # New EnhancedConfig tests
├── test_models.py           # Domain model tests
├── test_cli.py              # CLI integration tests
└── ...
```

#### Running Tests

No changes:
```bash
pytest
pytest --cov=az_pim_cli
pytest -k test_config
```

### Code Review Checklist

When reviewing code, check for:

- ✅ Uses `ruff format` and `ruff check`
- ✅ Imports from `domain/` for models/exceptions
- ✅ New HTTP code uses `HTTPXAdapter` or protocol
- ✅ Configuration uses `EnhancedConfig` for new features
- ✅ Type hints on all new functions
- ✅ Tests for new functionality

### Deprecation Timeline

| Version | Status | Action |
|---------|--------|--------|
| 0.1.0 | Current | Old imports work, no warnings |
| 0.2.0 | Planned | Deprecation warnings for old imports |
| 1.0.0 | Future | Remove old import shims |

### Common Pitfalls

#### 1. Direct Config Dictionary Access

**Don't:**
```python
config._config["aliases"]["prod"]  # Internal, may change
```

**Do:**
```python
config.get_alias("prod")  # Public API
```

#### 2. Importing from Root

**Don't:**
```python
from az_pim_cli import Config  # May not exist
```

**Do:**
```python
from az_pim_cli.config import Config  # Explicit path
```

#### 3. Skipping Type Hints

**Don't:**
```python
def process_role(role):  # Untyped
    ...
```

**Do:**
```python
from az_pim_cli.domain.models import NormalizedRole

def process_role(role: NormalizedRole) -> bool:
    ...
```

### Getting Help

- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Changelog**: See [CHANGELOG.md](../CHANGELOG.md)
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

## Quick Reference

### Command Changes

| Old Command | New Command | Notes |
|-------------|-------------|-------|
| `black src/` | `ruff format src/` | Faster |
| `isort src/` | `ruff check --fix src/` | Combined |
| `flake8 src/` | `ruff check src/` | More checks |

### Import Changes

| Old Import | New Import | Status |
|------------|------------|--------|
| `from az_pim_cli.config import Config` | `from az_pim_cli.infra.config_adapter import EnhancedConfig` | Both work |
| `from az_pim_cli.models import *` | `from az_pim_cli.domain.models import *` | Both work |
| `from az_pim_cli.exceptions import *` | `from az_pim_cli.domain.exceptions import *` | Both work |

### New Features

| Feature | Module | Description |
|---------|--------|-------------|
| HTTP Retry | `infra.http_client_adapter` | Automatic retry/backoff |
| Config Validation | `infra.config_adapter` | Pydantic validation |
| Protocols | `interfaces.*` | Swappable implementations |

## Examples

### Migrating a Module

**Before:**
```python
from az_pim_cli.config import Config
from az_pim_cli.models import NormalizedRole
import requests

def fetch_data():
    config = Config()
    url = "https://api.example.com"
    response = requests.get(url)
    return response.json()
```

**After:**
```python
from az_pim_cli.infra.config_adapter import EnhancedConfig
from az_pim_cli.domain.models import NormalizedRole
from az_pim_cli.infra.http_client_adapter import HTTPXAdapter

def fetch_data() -> dict:
    config = EnhancedConfig()
    http_client = HTTPXAdapter()
    url = "https://api.example.com"
    return http_client.get(url)
```

**Benefits:**
- Automatic retry
- Type hints
- Validated config

### Adding a New Feature

**Use the new architecture:**

1. Define domain model in `domain/`
2. Create protocol in `interfaces/` if needed
3. Implement adapter in `infra/`
4. Use from `cli.py` or services

**Example:**
```python
# 1. Domain model
from az_pim_cli.domain.models import NormalizedRole

# 2. Protocol (optional)
from az_pim_cli.interfaces.http_client import HTTPClientProtocol

# 3. Adapter
from az_pim_cli.infra.http_client_adapter import HTTPXAdapter

# 4. Use it
client = HTTPXAdapter()
data = client.get("...")
```

## Conclusion

The new architecture provides:
- ✅ Better separation of concerns
- ✅ Swappable implementations
- ✅ Enhanced reliability (retry, validation)
- ✅ Faster development (ruff)
- ✅ Type safety (Pydantic, mypy)

While maintaining:
- ✅ Backward compatibility
- ✅ Existing CLI behavior
- ✅ Configuration format
