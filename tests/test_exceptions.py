"""Tests for domain exceptions."""

from az_pim_cli.domain.exceptions import (
    AuthenticationError,
    NetworkError,
    ParsingError,
    PermissionError,
    PIMError,
)


class TestPIMError:
    """Tests for base PIMError."""

    def test_pim_error_creation(self):
        """Test creating base PIMError."""
        error = PIMError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert isinstance(error, Exception)


class TestNetworkError:
    """Tests for NetworkError."""

    def test_network_error_basic(self):
        """Test creating NetworkError with just a message."""
        error = NetworkError("Connection failed")
        assert str(error) == "Connection failed"
        assert error.endpoint == ""
        assert error.suggest_ipv4 is False

    def test_network_error_with_endpoint(self):
        """Test creating NetworkError with endpoint."""
        error = NetworkError("Connection failed", endpoint="https://graph.microsoft.com")
        assert str(error) == "Connection failed"
        assert error.endpoint == "https://graph.microsoft.com"

    def test_network_error_with_ipv4_suggestion(self):
        """Test creating NetworkError with IPv4 suggestion."""
        error = NetworkError(
            "DNS resolution failed", endpoint="https://graph.microsoft.com", suggest_ipv4=True
        )
        assert error.suggest_ipv4 is True


class TestPermissionError:
    """Tests for PermissionError."""

    def test_permission_error_basic(self):
        """Test creating PermissionError with just a message."""
        error = PermissionError("Access denied")
        assert str(error) == "Access denied"
        assert error.endpoint == ""
        assert error.required_permissions == ""

    def test_permission_error_with_details(self):
        """Test creating PermissionError with all details."""
        error = PermissionError(
            "Access denied",
            endpoint="/roleManagement/directory",
            required_permissions="RoleManagement.ReadWrite.Directory",
        )
        assert str(error) == "Access denied"
        assert error.endpoint == "/roleManagement/directory"
        assert error.required_permissions == "RoleManagement.ReadWrite.Directory"


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_authentication_error_basic(self):
        """Test creating AuthenticationError with just a message."""
        error = AuthenticationError("Auth failed")
        assert str(error) == "Auth failed"
        assert error.suggestion == ""

    def test_authentication_error_with_suggestion(self):
        """Test creating AuthenticationError with suggestion."""
        error = AuthenticationError("Auth failed", suggestion="Run 'az login'")
        assert str(error) == "Auth failed"
        assert error.suggestion == "Run 'az login'"


class TestParsingError:
    """Tests for ParsingError."""

    def test_parsing_error_basic(self):
        """Test creating ParsingError with just a message."""
        error = ParsingError("Failed to parse response")
        assert str(error) == "Failed to parse response"
        assert error.response_data == ""

    def test_parsing_error_with_response_data(self):
        """Test creating ParsingError with response data."""
        error = ParsingError("Failed to parse response", response_data='{"invalid": json')
        assert str(error) == "Failed to parse response"
        assert error.response_data == '{"invalid": json'
