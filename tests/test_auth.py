"""Tests for authentication and IPv4 context."""

import os
import socket
import pytest
from az_pim_cli.auth import should_use_ipv4_only, ipv4_only_context


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
