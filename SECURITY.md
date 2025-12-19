# Security Policy

## Overview

Security is a top priority for az-pim-cli, especially given its role in managing Azure Privileged Identity Management (PIM). We take all security vulnerabilities seriously and appreciate your efforts to responsibly disclose your findings.

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

**Note:** As the project matures, we will maintain security updates for the latest stable release and potentially the previous major version.

## Reporting a Vulnerability

**⚠️ IMPORTANT: Please DO NOT report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability, please report it privately using one of these methods:

### Preferred Method: GitHub Security Advisories

1. Go to the [Security](https://github.com/dkuwcreator/az-pim-cli/security) tab in the repository
2. Click "Report a vulnerability"
3. Fill in the details using the form provided

### Alternative Method: Email

If you cannot use GitHub Security Advisories, please email the maintainer directly:
- **Email:** Create a private issue and request security contact information

### What to Include in Your Report

Please provide the following information to help us understand and address the vulnerability:

1. **Type of vulnerability** (e.g., credential exposure, injection attack, privilege escalation)
2. **Location** (file path, function name, line number if applicable)
3. **Step-by-step reproduction instructions**
4. **Proof of concept or exploit code** (if possible)
5. **Impact assessment** (what an attacker could do with this vulnerability)
6. **Suggested fix** (if you have one)
7. **Your contact information** for follow-up questions

### What to Expect

- **Acknowledgment:** We will acknowledge receipt of your report within 48 hours
- **Communication:** We will keep you informed of our progress
- **Timeline:** We aim to address critical vulnerabilities within 7 days, high severity within 30 days
- **Credit:** We will credit you in the security advisory (unless you prefer to remain anonymous)
- **Disclosure:** We follow a coordinated disclosure process and will work with you on the timing

## Security Best Practices for Contributors

When contributing to az-pim-cli, please follow these security guidelines:

### 1. Never Commit Secrets

- **No hardcoded credentials:** Never commit API keys, tokens, passwords, or other secrets
- **Use environment variables:** Store sensitive configuration in environment variables
- **Check before commit:** Review your changes for accidentally included secrets
- **Use .gitignore:** Ensure sensitive files are excluded from version control

Example of what NOT to do:
```python
# ❌ BAD - Never do this
CLIENT_SECRET = "abc123-secret-key-xyz789"
```

Example of proper approach:
```python
# ✅ GOOD - Use environment variables
import os
CLIENT_SECRET = os.environ.get("AZURE_CLIENT_SECRET")
```

### 2. Input Validation

- **Validate all user input:** Never trust user input without validation
- **Use type hints:** Leverage Python's type system for basic validation
- **Sanitize inputs:** Clean and validate inputs before using them in commands or API calls
- **Fail securely:** Handle invalid input gracefully without exposing system details

Example:
```python
def validate_duration(duration: int) -> int:
    """Validate PIM role activation duration."""
    if not isinstance(duration, int):
        raise ValueError("Duration must be an integer")
    if not 1 <= duration <= 24:
        raise ValueError("Duration must be between 1 and 24 hours")
    return duration
```

### 3. Dependency Management

- **Keep dependencies updated:** Regularly update dependencies to patch known vulnerabilities
- **Review new dependencies:** Carefully evaluate new dependencies before adding them
- **Use Dependabot:** We use Dependabot to automatically detect vulnerable dependencies
- **Pin versions:** Use specific version ranges in `pyproject.toml`
- **Audit dependencies:** Run `pip-audit` or similar tools to check for known vulnerabilities

### 4. Authentication and Authorization

- **Use Azure SDK authentication:** Leverage Azure Identity SDK for secure authentication
- **Follow least privilege:** Only request the minimum permissions needed
- **Token handling:** Never log or expose authentication tokens
- **Session management:** Properly manage and invalidate sessions

### 5. Code Review

- **All changes require review:** No direct commits to `main` branch
- **Security-focused reviews:** Reviewers should specifically look for security issues
- **Automated checks:** Our CI/CD pipeline includes security scanning (Bandit)
- **Test security features:** Include tests that verify security controls

### 6. Error Handling and Logging

- **Don't expose sensitive data:** Error messages and logs should not contain secrets or PII
- **Handle exceptions properly:** Catch and handle exceptions gracefully
- **Log security events:** Log authentication attempts and authorization decisions
- **Sanitize logs:** Remove or redact sensitive information from logs

Example:
```python
try:
    result = activate_role(role_name, token)
except Exception as e:
    # ❌ BAD - Don't log the full exception which might contain tokens
    # logger.error(f"Activation failed: {e}")
    
    # ✅ GOOD - Log without sensitive details
    logger.error(f"Role activation failed for {role_name}")
    raise
```

### 7. API Security

- **Use HTTPS:** All API calls should use HTTPS
- **Validate responses:** Verify API responses before using them
- **Rate limiting:** Implement rate limiting where appropriate
- **Timeout handling:** Set appropriate timeouts for API calls

## Security Features in az-pim-cli

### Current Security Measures

- **Azure SDK Integration:** Uses official Azure SDK for secure authentication
- **No credential storage:** Does not store credentials locally (relies on Azure CLI or MSAL)
- **Input validation:** Validates user inputs before making API calls
- **Type safety:** Uses Python type hints throughout
- **Dependency scanning:** Automated vulnerability scanning with Dependabot and Bandit

### Ongoing Security Improvements

We continuously work to improve security:
- Regular dependency updates
- Security-focused code reviews
- Automated security testing in CI/CD
- Community security audits

## Security Scanning

Our CI/CD pipeline includes:
- **Bandit:** Static security analysis for Python code
- **Dependabot:** Automated dependency vulnerability detection
- **Code review:** Manual security review by maintainers

## Disclosure Policy

We follow a **coordinated disclosure** policy:
1. Security researchers report vulnerabilities privately
2. We work together to understand and fix the issue
3. We prepare a security advisory and patch
4. We coordinate on timing for public disclosure
5. We publicly disclose the vulnerability with credit to the researcher

## Acknowledgments

We would like to thank the following individuals for responsibly disclosing security vulnerabilities:

- (No vulnerabilities reported yet)

Thank you for helping keep az-pim-cli and its users safe! 🔒
