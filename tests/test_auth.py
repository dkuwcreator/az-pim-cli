"""Tests for authentication and IPv4 context."""

import os
import socket
import pytest
from unittest.mock import patch, MagicMock
from az_pim_cli.auth import should_use_ipv4_only, ipv4_only_context, AzureAuth
from az_pim_cli.exceptions import AuthenticationError


def test_should_use_ipv4_only_default():
    """Test IPv4-only detection with default (disabled)."""
    # Clear env var
    os.environ.pop("AZ_PIM_IPV4_ONLY", None)
    assert should_use_ipv4_only() is False


def test_should_use_ipv4_only_enabled():
    """Test IPv4-only detection when enabled."""
    test_values = ["1", "true", "True", "TRUE", "yes", "Yes", "YES"]
    for value in test_values:
        os.environ["AZ_PIM_IPV4_ONLY"] = value
        assert should_use_ipv4_only() is True, f"Failed for value: {value}"

    # Clean up
    os.environ.pop("AZ_PIM_IPV4_ONLY", None)


def test_should_use_ipv4_only_disabled():
    """Test IPv4-only detection when explicitly disabled."""
    test_values = ["0", "false", "False", "no", "No", ""]
    for value in test_values:
        os.environ["AZ_PIM_IPV4_ONLY"] = value
        assert should_use_ipv4_only() is False, f"Failed for value: {value}"

    # Clean up
    os.environ.pop("AZ_PIM_IPV4_ONLY", None)


def test_ipv4_only_context():
    """Test IPv4-only context manager."""
    original_getaddrinfo = socket.getaddrinfo

    # Before context
    assert socket.getaddrinfo is original_getaddrinfo

    # Inside context
    with ipv4_only_context():
        assert socket.getaddrinfo is not original_getaddrinfo
        # Test that it forces IPv4
        # We can't easily test the actual behavior without network calls,
        # but we can verify the function was replaced

    # After context (should be restored)
    assert socket.getaddrinfo is original_getaddrinfo


def test_ipv4_only_context_exception_handling():
    """Test that IPv4 context restores socket.getaddrinfo even on exception."""
    original_getaddrinfo = socket.getaddrinfo

    try:
        with ipv4_only_context():
            assert socket.getaddrinfo is not original_getaddrinfo
            raise ValueError("Test exception")
    except ValueError:
        pass

    # Should be restored even after exception
    assert socket.getaddrinfo is original_getaddrinfo


def test_azure_auth_initialization():
    """Test that AzureAuth initializes without errors."""
    auth = AzureAuth()
    assert auth is not None
    assert auth._credential is None
    assert auth._default_credential is None


@patch("az_pim_cli.auth.AzureCliCredential")
def test_azure_auth_get_token_with_cli_credential(mock_cli_cred_class):
    """Test token acquisition with AzureCliCredential."""
    mock_token = MagicMock()
    mock_token.token = "test-token-value"
    mock_cred = MagicMock()
    mock_cred.get_token.return_value = mock_token
    mock_cli_cred_class.return_value = mock_cred

    auth = AzureAuth()
    token = auth.get_token()

    assert token == "test-token-value"
    mock_cred.get_token.assert_called()


@patch("az_pim_cli.auth.DefaultAzureCredential")
@patch("az_pim_cli.auth.AzureCliCredential")
def test_azure_auth_fallback_to_default_credential(mock_cli_cred_class, mock_default_cred_class):
    """Test fallback to DefaultAzureCredential when AzureCliCredential fails."""
    # AzureCliCredential fails
    mock_cli_cred_class.side_effect = Exception("CLI not available")

    # DefaultAzureCredential succeeds
    mock_token = MagicMock()
    mock_token.token = "test-token-value"
    mock_default_cred = MagicMock()
    mock_default_cred.get_token.return_value = mock_token
    mock_default_cred_class.return_value = mock_default_cred

    auth = AzureAuth()
    token = auth.get_token()

    assert token == "test-token-value"
    mock_default_cred.get_token.assert_called()


def test_extract_token_claim_from_jwt():
    """Test extracting claims from JWT token."""
    # Create a mock token with JWT structure
    # JWT format: header.payload.signature
    # Payload: {"oid": "user-123", "tid": "tenant-456"}
    import json
    import base64

    payload = {"oid": "user-123", "tid": "tenant-456"}
    payload_json = json.dumps(payload).encode()
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode().rstrip("=")
    mock_token = f"header.{payload_b64}.signature"

    # Mock get_token to return our test token
    auth = AzureAuth()
    with patch.object(auth, "get_token", return_value=mock_token):
        oid = auth._extract_token_claim("https://graph.microsoft.com/.default", "oid")
        tid = auth._extract_token_claim("https://management.azure.com/.default", "tid")

        assert oid == "user-123"
        assert tid == "tenant-456"


def test_extract_token_claim_missing_claim():
    """Test extracting a claim that doesn't exist."""
    import json
    import base64

    payload = {"oid": "user-123"}
    payload_json = json.dumps(payload).encode()
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode().rstrip("=")
    mock_token = f"header.{payload_b64}.signature"

    auth = AzureAuth()
    with patch.object(auth, "get_token", return_value=mock_token):
        result = auth._extract_token_claim("https://graph.microsoft.com/.default", "missing")
        assert result is None


def test_get_user_object_id_from_token():
    """Test getting user object ID from token."""
    import json
    import base64

    payload = {"oid": "user-object-123"}
    payload_json = json.dumps(payload).encode()
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode().rstrip("=")
    mock_token = f"header.{payload_b64}.signature"

    auth = AzureAuth()
    with patch.object(auth, "get_token", return_value=mock_token):
        oid = auth.get_user_object_id()
        assert oid == "user-object-123"


def test_get_tenant_id_from_token():
    """Test getting tenant ID from token."""
    import json
    import base64

    payload = {"tid": "tenant-456"}
    payload_json = json.dumps(payload).encode()
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode().rstrip("=")
    mock_token = f"header.{payload_b64}.signature"

    auth = AzureAuth()
    with patch.object(auth, "get_token", return_value=mock_token):
        tid = auth.get_tenant_id()
        assert tid == "tenant-456"

