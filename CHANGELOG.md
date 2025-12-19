# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Clean architecture with domain/app/infra separation
- Pydantic-based configuration with validation
- Enhanced HTTP client with retry/backoff using httpx and tenacity
- Strict type checking with mypy
- Comprehensive type hints across all modules
- Ruff for faster linting and formatting (replaces black, isort, flake8)

### Changed
- **BREAKING**: Migrated from `requests` to `httpx` for HTTP operations
  - HTTP operations now use httpx's API
  - Adapter pattern isolates HTTP implementation for future swappability
- Replaced black + isort + flake8 with ruff for improved developer experience
- Enhanced mypy configuration for stricter type checking
- Configuration now supports Pydantic models for better validation
- Improved error messages with detailed validation feedback

### Deprecated
- Direct usage of `config.Config._config` dictionary (use typed accessors instead)
- Raw PyYAML access patterns (Pydantic models provide better validation)

### Removed
- Unused dependencies (replaced with more maintained alternatives)

### Fixed
- All mypy type errors resolved
- Improved type safety across the codebase

### Security
- Updated dependencies to latest versions
- Enhanced input validation with Pydantic

## [0.1.0] - Previous Release

### Added
- Initial release with Azure PIM CLI functionality
- Support for Azure AD and Resource roles
- Alias management
- Smart input resolution with fuzzy matching
- Interactive selection mode
- Configuration file support
