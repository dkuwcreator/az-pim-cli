# Security

## Reporting Security Issues

If you discover a security vulnerability in az-pim-cli, please report it privately to the maintainers. 

**DO NOT** create a public GitHub issue for security vulnerabilities.

## Security Best Practices

### Authentication
- Uses Azure Identity SDK credential chain
- No credentials are stored locally
- Supports managed identity for production environments
- Azure CLI integration for development

### Input Validation
- All inputs validated with Pydantic models
- Type safety enforced with mypy strict mode
- Fuzzy matching threshold prevents resource exhaustion

### Dependencies
- Regular security scanning with bandit
- Dependency auditing with pip-audit
- Automated updates via Dependabot
- Minimal dependency footprint

### Code Quality
- Strict type checking prevents injection vulnerabilities
- No use of `eval()` or `exec()`
- Safe YAML loading (yaml.safe_load)
- No shell command execution with user input

## Known Security Considerations

### System Dependencies

Some security vulnerabilities may appear in system-installed Python packages (like urllib3 from Ubuntu packages). These are outside the control of az-pim-cli but are noted here for transparency:

- urllib3 2.0.7 (system package) has known CVEs. Recommend using a virtual environment with updated packages.
- Azure SDK dependencies are regularly updated but may have transient vulnerabilities

### Mitigation Steps

1. **Use Virtual Environments**: Always install az-pim-cli in a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install az-pim-cli
   ```

2. **Keep Dependencies Updated**: Regularly update dependencies
   ```bash
   pip install --upgrade az-pim-cli
   ```

3. **Monitor Security Advisories**: Subscribe to GitHub security advisories for this repository

4. **Run Security Scans**: Use pip-audit to check for vulnerabilities
   ```bash
   pip install pip-audit
   python -m pip_audit
   ```

## Security Tools

This project uses the following security tools:

- **bandit**: Static security analysis for Python code
- **pip-audit**: Dependency vulnerability scanning
- **mypy**: Type safety to prevent runtime errors
- **ruff**: Linting including security checks
- **pre-commit**: Automated security checks on commit

## Security Updates

Security updates are released as soon as possible after discovery. Always use the latest version.

## Contact

For security-related questions or concerns, please open a private security advisory on GitHub.
