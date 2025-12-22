"""Tests for Graph and ARM provider modules."""

from unittest.mock import MagicMock, patch

import pytest

from az_pim_cli.auth import AzureAuth
from az_pim_cli.providers import AzureARMProvider, EntraGraphProvider


class TestProviderImports:
    """Test that provider modules can be imported."""

    def test_import_providers_from_package(self):
        """Test importing providers from top-level package."""
        # These imports test that providers/__init__.py works
        assert EntraGraphProvider is not None
        assert AzureARMProvider is not None


class TestEntraGraphProvider:
    """Tests for EntraGraphProvider."""

    @patch("az_pim_cli.auth.azurecli.AzureCliCredential")
    def test_initialization(self, mock_cred):
        """Test provider initialization."""
        mock_cred.return_value = MagicMock()
        auth = AzureAuth()
        provider = EntraGraphProvider(auth=auth)
        assert provider is not None
        assert provider.auth == auth
        assert provider.GRAPH_API_BETA == "https://graph.microsoft.com/beta"

    @patch("az_pim_cli.auth.azurecli.AzureCliCredential")
    def test_initialization_with_verbose(self, mock_cred):
        """Test provider initialization with verbose flag."""
        mock_cred.return_value = MagicMock()
        auth = AzureAuth()
        provider = EntraGraphProvider(auth=auth, verbose=True)
        assert provider.verbose is True

    @patch("az_pim_cli.auth.azurecli.AzureCliCredential")
    def test_get_headers(self, mock_cred):
        """Test getting request headers."""
        mock_token = MagicMock()
        mock_token.token = "test-token-value"
        mock_cred_instance = MagicMock()
        mock_cred_instance.get_token.return_value = mock_token
        mock_cred.return_value = mock_cred_instance

        auth = AzureAuth()
        provider = EntraGraphProvider(auth=auth)
        headers = provider._get_headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-token-value"
        assert "Content-Type" in headers


class TestAzureARMProvider:
    """Tests for AzureARMProvider."""

    @patch("az_pim_cli.auth.azurecli.AzureCliCredential")
    def test_initialization(self, mock_cred):
        """Test provider initialization."""
        mock_cred.return_value = MagicMock()
        auth = AzureAuth()
        provider = AzureARMProvider(auth=auth)
        assert provider is not None
        assert provider.auth == auth
        assert provider.ARM_API_BASE == "https://management.azure.com"
        assert provider.API_VERSION == "2020-10-01"

    @patch("az_pim_cli.auth.azurecli.AzureCliCredential")
    def test_initialization_with_verbose(self, mock_cred):
        """Test provider initialization with verbose flag."""
        mock_cred.return_value = MagicMock()
        auth = AzureAuth()
        provider = AzureARMProvider(auth=auth, verbose=True)
        assert provider.verbose is True

    @patch("az_pim_cli.auth.azurecli.AzureCliCredential")
    def test_get_headers(self, mock_cred):
        """Test getting request headers."""
        mock_token = MagicMock()
        mock_token.token = "test-arm-token"
        mock_cred_instance = MagicMock()
        mock_cred_instance.get_token.return_value = mock_token
        mock_cred.return_value = mock_cred_instance

        auth = AzureAuth()
        provider = AzureARMProvider(auth=auth)
        headers = provider._get_headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-arm-token"
        assert "Content-Type" in headers


