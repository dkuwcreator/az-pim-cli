"""Custom exceptions for Azure PIM CLI."""


class PIMError(Exception):
    """Base exception for PIM CLI errors."""
    pass


class NetworkError(PIMError):
    """Network-related errors (DNS, timeout, connection)."""
    
    def __init__(self, message: str, endpoint: str = "", suggest_ipv4: bool = False):
        self.endpoint = endpoint
        self.suggest_ipv4 = suggest_ipv4
        super().__init__(message)


class PermissionError(PIMError):
    """Permission-related errors (403, authorization)."""
    
    def __init__(self, message: str, endpoint: str = "", required_permissions: str = ""):
        self.endpoint = endpoint
        self.required_permissions = required_permissions
        super().__init__(message)


class AuthenticationError(PIMError):
    """Authentication errors (expired token, login required)."""
    
    def __init__(self, message: str, suggestion: str = ""):
        self.suggestion = suggestion
        super().__init__(message)


class ParsingError(PIMError):
    """Response parsing errors."""
    
    def __init__(self, message: str, response_data: str = ""):
        self.response_data = response_data
        super().__init__(message)
