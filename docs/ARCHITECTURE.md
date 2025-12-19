# Architecture Documentation

## Overview

az-pim-cli follows a **Clean Architecture** pattern with clear separation of concerns, making the codebase maintainable, testable, and extensible.

## Project Structure

```
src/az_pim_cli/
├── domain/              # Pure business logic
│   ├── models.py       # Domain entities (NormalizedRole, RoleSource)
│   └── exceptions.py   # Domain exceptions (PIMError, NetworkError, etc.)
│
├── interfaces/          # Protocol definitions (ports)
│   ├── http_client.py  # HTTPClientProtocol
│   └── config.py       # ConfigProtocol
│
├── infra/              # Infrastructure adapters
│   ├── http_client_adapter.py  # HTTPXAdapter (httpx + tenacity)
│   └── config_adapter.py       # EnhancedConfig (Pydantic-based)
│
├── app/                # Application services (future: use cases)
│
├── cli.py              # CLI entry point and commands
├── pim_client.py       # PIM API client
├── resolver.py         # Input resolution logic
├── auth.py             # Azure authentication
├── config.py           # Legacy config (backward compat shim)
├── models.py           # Legacy models (backward compat shim)
└── exceptions.py       # Legacy exceptions (backward compat shim)
```

## Architecture Layers

### Domain Layer (`domain/`)

**Pure business logic with no external dependencies.**

- **Models**: Business entities like `NormalizedRole`, `RoleSource`
- **Exceptions**: Domain-specific errors
- **Benefits**: 
  - Easy to test (no mocking required)
  - Reusable across different infrastructures
  - Clear business rules

### Interfaces Layer (`interfaces/`)

**Protocol definitions (ports) for dependency inversion.**

- Defines contracts without implementations
- Examples: `HTTPClientProtocol`, `ConfigProtocol`
- **Benefits**:
  - Swappable implementations
  - Testability (mock implementations)
  - Flexibility (try different libraries)

### Infrastructure Layer (`infra/`)

**Adapters for external services and libraries.**

- **HTTPXAdapter**: Modern HTTP client using httpx with automatic retry/backoff (tenacity)
- **EnhancedConfig**: Pydantic-based configuration with validation
- **Benefits**:
  - Isolates external dependencies
  - Easy to replace implementations
  - Enhanced error handling

### Application Layer (`app/`)

**Use cases and application services (future expansion).**

Currently minimal, but structured for growth:
- Service orchestration
- Business workflows
- Transaction boundaries

### Presentation Layer (CLI)

**User interface and command handling.**

- `cli.py`: Typer-based CLI commands
- Rich console output
- User input handling

## Dependency Flow

```
CLI → PIM Client → Infrastructure Adapters → External Services
 ↓         ↓              ↓
Domain ← Interfaces ← Infrastructure
```

**Key Principle**: Dependencies point inward (toward domain).

## Design Patterns

### 1. **Adapter Pattern**

Infrastructure implementations adapt external libraries to internal protocols.

```python
# Protocol (interface)
class HTTPClientProtocol(Protocol):
    def get(self, url: str) -> Dict[str, Any]: ...

# Adapter (implementation)
class HTTPXAdapter:
    """Adapts httpx to HTTPClientProtocol."""
    def get(self, url: str) -> Dict[str, Any]:
        # Uses httpx internally
        ...
```

### 2. **Dependency Injection**

Components receive dependencies through constructors.

```python
class PIMClient:
    def __init__(self, auth: AzureAuth, http_client: HTTPClientProtocol):
        self.auth = auth
        self.http_client = http_client
```

### 3. **Repository Pattern** (Implicit)

Configuration acts as a repository for settings and aliases.

### 4. **Strategy Pattern** (Resolver)

Different matching strategies (exact, fuzzy, prefix) selected at runtime.

## Technology Choices

### Why httpx?

- ✅ Modern, actively maintained (latest: Dec 2024)
- ✅ Better async support than requests
- ✅ HTTP/2 support
- ✅ Cleaner API
- ✅ Better timeout handling

### Why tenacity?

- ✅ Robust retry/backoff logic
- ✅ Configurable strategies
- ✅ Works with both sync and async
- ✅ Battle-tested

### Why Pydantic?

- ✅ Type-safe configuration
- ✅ Automatic validation
- ✅ Environment variable support
- ✅ JSON schema generation
- ✅ Excellent error messages

### Why ruff?

- ✅ 10-100x faster than black+flake8+isort
- ✅ Single tool replaces three
- ✅ Rapidly adopted by Python community
- ✅ Compatible with Black formatting

## Backward Compatibility

Original modules (`config.py`, `models.py`, `exceptions.py`) are now **compatibility shims** that re-export from the new structure:

```python
# config.py (legacy)
from az_pim_cli.infra.config_adapter import EnhancedConfig as Config
```

**Migration Path**:
1. Old imports continue to work
2. New code uses new paths
3. Deprecation warnings guide developers
4. Future version can remove shims

## Testing Strategy

### Unit Tests

- Domain logic: No mocking needed
- Adapters: Mock external calls
- CLI: Mock client interactions

### Integration Tests

- Config loading/saving
- HTTP retry behavior
- End-to-end CLI commands

### Test Coverage

Current: 88 tests, all passing ✅

```bash
pytest --cov=az_pim_cli
```

## Future Enhancements

1. **Service Layer**: Move business logic from CLI to `app/services/`
2. **Repository Layer**: Abstract data access patterns
3. **Event Bus**: Decouple components with events
4. **Async Support**: Leverage httpx async capabilities
5. **Plugin System**: Allow extensions via adapters

## Benefits Achieved

✅ **Maintainability**: Clear boundaries, easy to navigate
✅ **Testability**: Pure functions, mockable adapters
✅ **Flexibility**: Swappable implementations
✅ **Type Safety**: Pydantic + mypy catch errors early
✅ **Performance**: Ruff speeds up development
✅ **Reliability**: Automatic retries, validation
✅ **Backward Compatibility**: Existing code works unchanged

## References

- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Dependency Inversion Principle](https://en.wikipedia.org/wiki/Dependency_inversion_principle)
