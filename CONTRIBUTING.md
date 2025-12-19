# Contributing to az-pim-cli

Thank you for your interest in contributing to az-pim-cli! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## How to Report Bugs

If you find a bug in the project, please help us by submitting an issue using our bug report template:

1. Go to the [Issues](https://github.com/dkuwcreator/az-pim-cli/issues) page
2. Click "New Issue"
3. Select the "Bug Report" template
4. Fill in all required information:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs. actual behavior
   - Environment details (OS, Python version, az-pim-cli version)
   - Any relevant logs or screenshots

**Security Note:** If you discover a security vulnerability, please DO NOT open a public issue. Instead, follow the responsible disclosure process outlined in [SECURITY.md](SECURITY.md).

## How to Suggest Enhancements

We welcome feature requests and enhancement suggestions! To suggest an enhancement:

1. Go to the [Issues](https://github.com/dkuwcreator/az-pim-cli/issues) page
2. Click "New Issue"
3. Select the "Feature Request" template
4. Provide detailed information:
   - Clear description of the proposed feature
   - Use case and motivation
   - Proposed solution or implementation approach
   - Any alternative solutions you've considered

## Pull Request Process

### Before You Start

1. **Check existing issues and PRs** to avoid duplicate work
2. **Open an issue first** for significant changes to discuss the approach
3. **Fork the repository** to your own GitHub account
4. **Create a feature branch** from `main` with a descriptive name:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

### Development Setup

1. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR-USERNAME/az-pim-cli.git
   cd az-pim-cli
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks (recommended):**
   ```bash
   pre-commit install
   ```

### Making Changes

1. **Write your code** following our coding standards (see below)
2. **Add or update tests** to cover your changes
3. **Run tests locally** to ensure everything passes:
   ```bash
   pytest
   ```
4. **Run linters and formatters:**
   ```bash
   black src/ tests/
   isort src/ tests/
   flake8 src/ tests/
   mypy src/
   ```

### Coding Standards

This project follows these coding standards:

- **PEP 8:** Follow Python's official style guide
- **Type Hints:** Use type hints for all function signatures
- **Docstrings:** Write clear docstrings for all public functions, classes, and modules
  - Use Google or NumPy style docstrings
  - Include parameter descriptions, return types, and examples where helpful
- **Line Length:** Maximum 100 characters (configured in black)
- **Import Organization:** Use isort to organize imports
- **Code Formatting:** Use black for consistent code formatting

Example:
```python
def activate_role(role_name: str, duration: int = 8) -> dict:
    """
    Activate an Azure PIM role.

    Args:
        role_name: The name of the role to activate
        duration: Duration in hours (default: 8)

    Returns:
        dict: The activation response from Azure API

    Raises:
        ValueError: If duration is not between 1 and 24 hours
    """
    # Implementation here
    pass
```

### Testing Requirements

- **All new features** must include unit tests
- **All bug fixes** should include a test that reproduces the bug
- **Aim for high coverage** (we strive for >80% code coverage)
- **Use pytest** for writing tests
- **Mock external dependencies** (Azure API calls, etc.)

Example test structure:
```python
def test_activate_role_success():
    """Test successful role activation."""
    # Arrange
    role_name = "Test Role"
    duration = 8
    
    # Act
    result = activate_role(role_name, duration)
    
    # Assert
    assert result["status"] == "success"
```

### Submitting a Pull Request

1. **Commit your changes** with clear, descriptive messages:
   ```bash
   git commit -m "Add feature: role activation history export"
   ```

2. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Open a Pull Request:**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill in the PR template completely
   - Link any related issues using keywords (e.g., "Fixes #123")

### Pull Request Guidelines

- **Keep changes focused:** One PR should address one feature or fix
- **Write clear commit messages:** Use present tense ("Add feature" not "Added feature")
- **Reference issues:** Link related issues in your PR description
- **Update documentation:** Include doc updates for new features
- **Ensure CI passes:** All automated checks must pass before merge
- **Be responsive:** Address review comments promptly
- **Small PRs:** Prefer smaller, focused PRs over large, sweeping changes

### Review Process

1. Maintainers will review your PR
2. Address any requested changes
3. Once approved, a maintainer will merge your PR
4. Your contribution will be included in the next release!

## Development Workflow

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=az_pim_cli --cov-report=html

# Run specific test file
pytest tests/test_cli.py

# Run specific test
pytest tests/test_cli.py::test_specific_function
```

### Code Quality Checks
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Security scan
bandit -r src/
```

### Running the CLI Locally
```bash
# After installing with pip install -e ".[dev]"
az-pim --help

# Or run directly
python -m az_pim_cli.cli --help
```

## Questions?

If you have questions about contributing, feel free to:
- Open a discussion in the [Discussions](https://github.com/dkuwcreator/az-pim-cli/discussions) section
- Ask in an issue or PR
- Reach out to the maintainers

Thank you for contributing to az-pim-cli! 🎉
