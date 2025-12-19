"""Tests for scope resolution in CLI."""

from unittest.mock import MagicMock

import pytest

from az_pim_cli.cli import resolve_scope_input


@pytest.fixture
def mock_auth():
    """Mock AzureAuth instance."""
    auth = MagicMock()
    auth.get_subscription_id.return_value = "12345678-1234-1234-1234-123456789abc"
    return auth


def test_resolve_full_subscription_path(mock_auth):
    """Test that full subscription paths are preserved."""
    scope = "/subscriptions/87654321-4321-4321-4321-210987654321"
    result = resolve_scope_input(scope, mock_auth)
    assert result == scope


def test_resolve_subscription_path_without_slash(mock_auth):
    """Test subscription paths without leading slash."""
    scope = "subscriptions/87654321-4321-4321-4321-210987654321"
    result = resolve_scope_input(scope, mock_auth)
    assert result == "/subscriptions/87654321-4321-4321-4321-210987654321"


def test_resolve_full_resource_group_path(mock_auth):
    """Test that full resource group paths are preserved."""
    scope = "/subscriptions/87654321-4321-4321-4321-210987654321/resourceGroups/my-rg"
    result = resolve_scope_input(scope, mock_auth)
    assert result == scope


def test_resolve_resource_group_name(mock_auth):
    """Test that resource group names are expanded to full paths."""
    scope = "Epac-dev"
    result = resolve_scope_input(scope, mock_auth)
    expected = "/subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/Epac-dev"
    assert result == expected


def test_resolve_resource_group_name_with_hyphens(mock_auth):
    """Test resource group names with hyphens."""
    scope = "my-prod-rg"
    result = resolve_scope_input(scope, mock_auth)
    expected = "/subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/my-prod-rg"
    assert result == expected


def test_resolve_resource_group_name_with_underscores(mock_auth):
    """Test resource group names with underscores."""
    scope = "my_dev_rg"
    result = resolve_scope_input(scope, mock_auth)
    expected = "/subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/my_dev_rg"
    assert result == expected


def test_resolve_partial_path_with_subscriptions(mock_auth):
    """Test partial paths that contain 'subscriptions/'."""
    scope = "subscriptions/87654321-4321-4321-4321-210987654321/resourceGroups/test"
    result = resolve_scope_input(scope, mock_auth)
    assert result == "/subscriptions/87654321-4321-4321-4321-210987654321/resourceGroups/test"


def test_resolve_provider_path(mock_auth):
    """Test that provider paths are preserved."""
    scope = "/providers/Microsoft.Management/managementGroups/my-group"
    result = resolve_scope_input(scope, mock_auth)
    assert result == scope


def test_resolve_complex_resource_path(mock_auth):
    """Test complex resource paths."""
    scope = "/subscriptions/12345/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm"
    result = resolve_scope_input(scope, mock_auth)
    assert result == scope


def test_resolve_case_preserved(mock_auth):
    """Test that case is preserved in resource group names."""
    scope = "MyResourceGroup"
    result = resolve_scope_input(scope, mock_auth)
    expected = "/subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/MyResourceGroup"
    assert result == expected
