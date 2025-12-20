# Architecture Overview

## Design Philosophy

The az-pim-cli follows clean architecture principles with a focus on:
- **Type Safety**: Strict mypy type checking ensures correctness
- **Modularity**: Clear separation of concerns
- **Testability**: Pure functions and dependency injection
- **Maintainability**: Standard tools and well-documented code

## Project Structure

```
az-pim-cli/
├── src/az_pim_cli/
│   ├── domain/          # Pure business logic (no external dependencies)
│   │   ├── models.py    # Domain models and data structures
│   │   └── exceptions.py # Domain-specific exceptions
│   ├── cli.py           # CLI entry point and commands (Typer)
│   ├── pim_client.py    # Azure PIM API client
│   ├── resolver.py      # Input resolution with fuzzy matching
│   ├── auth.py          # Authentication handling
│   ├── config.py        # Configuration management
│   ├── models.py        # Backward compatibility re-exports
│   └── exceptions.py    # Backward compatibility re-exports
├── tests/               # Comprehensive test suite
├── docs/                # Documentation
└── pyproject.toml       # Project configuration and dependencies
```

## Core Components

### Domain Layer (`domain/`)

**Purpose**: Pure business logic with no external dependencies

- **models.py**: Domain models using Pydantic for validation
  - `NormalizedRole`: Unified role representation across ARM and Graph APIs
  - `RoleSource`: Enum for API source tracking
  - Normalization functions for different API responses

- **exceptions.py**: Domain-specific exceptions
  - Clear error hierarchy for different failure modes
  - User-friendly error messages

**Design Principles**:
- No imports from infrastructure or application layers
- Pure functions where possible
- Immutable data structures using Pydantic
- Type-safe with mypy strict mode

### Application Layer

**cli.py** - Command-line interface
- Built with Typer for modern CLI UX
- Rich console for beautiful output
- Command structure:
  - `list`: Show eligible roles
  - `activate`: Activate a role
  - `history`: View activation history
  - `alias`: Manage role aliases
  - `pending`: List pending approvals
  - `approve`: Approve requests

**resolver.py** - Intelligent input resolution
- Multiple matching strategies:
  1. Exact match
  2. Case-insensitive match
  3. Prefix match
  4. Fuzzy match (with rapidfuzz or difflib)
- Caching for performance
- Interactive selection in TTY mode
- Non-interactive fallback for automation

**config.py** - Configuration management
- YAML-based configuration file
- Type-safe configuration access
- Alias management
- Default values with override support

### Infrastructure Layer

**pim_client.py** - Azure PIM API client
- Supports both ARM and Graph APIs
- Retry logic built into HTTP requests
- IPv4-only mode for DNS issues
- Comprehensive error handling
- Token caching

**auth.py** - Authentication
- Uses Azure Identity SDK
- Credential chain:
  1. Azure CLI credentials
  2. Default Azure credentials (managed identity, service principal, etc.)
- Token claim extraction
- IPv4-only DNS resolution context

## Data Flow

```
┌─────────────┐
│   CLI User  │
└──────┬──────┘
       │
       v
┌──────────────────┐
│  Typer Commands  │
│   (cli.py)       │
└────────┬─────────┘
         │
         v
┌─────────────────────┐
│  Input Resolver     │
│  (resolver.py)      │
└────────┬────────────┘
         │
         v
┌─────────────────────┐     ┌───────────────┐
│   PIM Client        │────>│   Azure       │
│  (pim_client.py)    │<────│   PIM API     │
└────────┬────────────┘     └───────────────┘
         │
         v
┌─────────────────────┐
│  Domain Models      │
│  (domain/models.py) │
└─────────────────────┘
```

## Key Design Decisions

### 1. Type Safety

**Decision**: Enforce strict type checking with mypy

**Rationale**:
- Catch errors at development time
- Better IDE support
- Self-documenting code
- Easier refactoring

**Implementation**:
```python
# pyproject.toml
[tool.mypy]
disallow_untyped_defs = true
warn_return_any = true
strict_equality = true
```

### 2. Domain Models

**Decision**: Use Pydantic for domain models

**Rationale**:
- Runtime validation
- Serialization/deserialization
- Type safety
- Documentation

**Example**:
```python
class NormalizedRole:
    name: str
    id: str
    status: str
    scope: str = ""
    source: RoleSource = RoleSource.ARM
    # ... additional fields
```

### 3. Configuration

**Decision**: YAML configuration with type-safe access

**Rationale**:
- Human-readable
- Supports complex structures
- Easy to version control
- Type-safe access methods

**Location**: `~/.az-pim-cli/config.yml`

### 4. Error Handling

**Decision**: Custom exception hierarchy with context

**Rationale**:
- Clear error messages
- Actionable suggestions
- Proper error categorization
- Easy to test

**Example**:
```python
class NetworkError(PIMError):
    def __init__(self, message: str, endpoint: str = "", suggest_ipv4: bool = False):
        super().__init__(message)
        self.endpoint = endpoint
        self.suggest_ipv4 = suggest_ipv4
```

### 5. Input Resolution

**Decision**: Multi-strategy matching with fallbacks

**Rationale**:
- User-friendly (typos, partial names)
- Deterministic behavior
- Performance (caching)
- Automation-friendly (exact match)

**Strategies**:
1. Exact → Fast, deterministic
2. Case-insensitive → Common user pattern
3. Prefix → Quick partial match
4. Fuzzy → Typo-tolerant

### 6. Testing

**Decision**: Comprehensive test coverage with pytest

**Rationale**:
- Confidence in changes
- Documentation through examples
- Prevent regressions
- Fast feedback

**Coverage**: 82 tests covering:
- CLI commands
- Input resolution
- Configuration
- Models
- Authentication

## Dependency Management

### Core Dependencies

- **typer[all]**: Modern CLI framework
- **azure-identity**: Azure authentication
- **azure-mgmt-subscription**: Subscription management
- **pydantic**: Data validation
- **pydantic-settings**: Settings management
- **pyyaml**: Configuration files
- **rich**: Terminal output
- **requests**: HTTP client (with plans to migrate to httpx)

### Optional Dependencies

- **rapidfuzz**: Fast fuzzy matching (recommended)
- **httpx**: Modern HTTP client (future)
- **tenacity**: Retry logic (future)

### Development Dependencies

- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **ruff**: Fast linter and formatter
- **mypy**: Static type checking
- **bandit**: Security scanning
- **pre-commit**: Git hooks
- **pip-audit**: Dependency security

## Security Considerations

1. **No credential storage**: Uses Azure SDK credential chain
2. **Type safety**: Prevents injection vulnerabilities
3. **Input validation**: Pydantic models validate all inputs
4. **Dependency scanning**: Automated with pip-audit and bandit
5. **Minimal permissions**: Uses least-privilege principle

## Performance Optimizations

1. **Caching**: Role lookups cached for 5 minutes (configurable)
2. **Pagination**: Handles large result sets efficiently
3. **Lazy loading**: Only fetch data when needed
4. **Connection pooling**: Reuses HTTP connections

## Future Improvements

1. **HTTP Client**: Migrate from requests to httpx
   - Better async support
   - Modern retry logic with tenacity
   - Type-safe API

2. **Structured Logging**: Replace debug prints with structlog
   - Contextual logging
   - JSON output option
   - Better debugging

3. **Dependency Injection**: Make components more testable
   - Easier mocking
   - Better separation
   - More flexible

4. **API Adapters**: Abstract API implementations
   - Swappable backends
   - Easier testing
   - Future-proof

## Contributing

When making changes:

1. **Type Safety**: Run `mypy src/` and fix all errors
2. **Tests**: Run `pytest tests/` and ensure 100% pass
3. **Linting**: Run `ruff check src/ tests/` and fix issues
4. **Formatting**: Run `ruff format src/ tests/`
5. **Security**: Run `bandit -r src/` to check for issues

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.

## References

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Azure Identity SDK](https://learn.microsoft.com/en-us/python/api/azure-identity/)
