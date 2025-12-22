# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive type hints across all modules with strict mypy enforcement
- Type stubs for external dependencies (`types-requests`)
- Enhanced mypy configuration with stricter checking
- Coverage thresholds in pytest configuration
- Bandit security scanning configuration
- pip-audit for dependency security scanning
- Optional dependencies for future HTTP/retry upgrades (`httpx`, `tenacity`)

### Changed
- **Type Safety**: Fixed all 47 mypy type errors for complete type coverage
- Improved type annotations in auth, config, resolver, pim_client, and cli modules
- Enhanced socket type handling with proper type ignores
- Refactored variable scoping to eliminate type confusion
- Updated test fixtures to use proper NormalizedRole instances
- Improved configuration value type conversions with explicit casts

### Fixed
- All mypy strict type checking errors resolved
- Socket getaddrinfo type compatibility issues
- Test compatibility with typed role objects
- Whitespace and import linting issues

### Security
- Added bandit configuration for security scanning
- Added pip-audit to dev dependencies for vulnerability checking
- Improved type safety reduces potential runtime errors

## [0.1.0] - Previous Release

### Added
- Initial release with Azure PIM CLI functionality
- Support for Azure AD and Resource roles
- Alias management
- Smart input resolution with fuzzy matching
- Interactive selection mode
- Configuration file support
