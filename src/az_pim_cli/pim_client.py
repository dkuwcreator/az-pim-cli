"""Azure PIM API client."""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

from az_pim_cli.auth import AzureAuth, ipv4_only_context, should_use_ipv4_only
from az_pim_cli.exceptions import NetworkError, PermissionError, ParsingError
from az_pim_cli.models import RoleSource


class PIMClient:
    """Client for interacting with Azure PIM APIs."""

    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
    GRAPH_API_BETA = "https://graph.microsoft.com/beta"
    ARM_API_BASE = "https://management.azure.com"

    def __init__(self, auth: Optional[AzureAuth] = None, verbose: bool = False) -> None:
        """
        Initialize PIM client.

        Args:
            auth: Azure authentication instance
            verbose: Enable verbose logging
        """
        self.auth = auth or AzureAuth()
        self.verbose = verbose
        self._backend = os.environ.get("AZ_PIM_BACKEND", "ARM").upper()
        
        if self.verbose:
            print(f"[DEBUG] PIM Client initialized with backend: {self._backend}")
            print(f"[DEBUG] IPv4-only mode: {should_use_ipv4_only()}")

    def _get_headers(self, scope: str = "https://graph.microsoft.com/.default") -> Dict[str, str]:
        """
        Get headers with authorization token.

        Args:
            scope: The scope for the access token

        Returns:
            Headers dictionary
        """
        token = self.auth.get_token(scope)
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    
    def _make_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        operation: str = "API request"
    ) -> Dict[str, Any]:
        """
        Make an HTTP request with enhanced error handling.
        
        Args:
            method: HTTP method (GET, POST, PUT)
            url: Request URL
            headers: Request headers
            params: Query parameters
            json_data: JSON body
            operation: Description of operation for error messages
            
        Returns:
            Response JSON data
            
        Raises:
            NetworkError: For DNS, timeout, and connection errors
            PermissionError: For 403 authorization errors
            ParsingError: For response parsing errors
        """
        def do_request():
            try:
                if self.verbose:
                    print(f"[DEBUG] {method} {url}")
                    if params:
                        print(f"[DEBUG] Params: {params}")
                
                if method == "GET":
                    response = requests.get(url, headers=headers, params=params, timeout=30)
                elif method == "POST":
                    response = requests.post(url, headers=headers, params=params, json=json_data, timeout=30)
                elif method == "PUT":
                    response = requests.put(url, headers=headers, params=params, json=json_data, timeout=30)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                if self.verbose:
                    print(f"[DEBUG] Response status: {response.status_code}")
                
                # Handle specific HTTP errors
                if response.status_code == 403:
                    principal_id = self.auth.get_user_object_id() if hasattr(self.auth, 'get_user_object_id') else "unknown"
                    raise PermissionError(
                        f"Permission denied for {operation}. "
                        f"Principal ID: {principal_id}. "
                        f"You may be missing required permissions.",
                        endpoint=url,
                        required_permissions="RoleManagement.ReadWrite.Directory or equivalent Azure RBAC permissions"
                    )
                elif response.status_code == 401:
                    from az_pim_cli.exceptions import AuthenticationError
                    raise AuthenticationError(
                        f"Authentication failed for {operation}",
                        suggestion="Run 'az login' to refresh your authentication"
                    )
                
                response.raise_for_status()
                
                try:
                    return response.json()
                except ValueError as e:
                    raise ParsingError(
                        f"Failed to parse JSON response for {operation}",
                        response_data=response.text[:500]
                    )
                    
            except requests.exceptions.ConnectionError as e:
                error_msg = str(e).lower()
                suggest_ipv4 = "getaddrinfo failed" in error_msg or "name resolution" in error_msg
                
                hint = ""
                if suggest_ipv4:
                    hint = " Try enabling IPv4-only mode: export AZ_PIM_IPV4_ONLY=1"
                
                raise NetworkError(
                    f"Connection error during {operation}: {str(e)}{hint}",
                    endpoint=url,
                    suggest_ipv4=suggest_ipv4
                )
            except requests.exceptions.Timeout:
                raise NetworkError(
                    f"Request timeout during {operation}. Check your network connection.",
                    endpoint=url
                )
            except requests.exceptions.RequestException as e:
                if hasattr(e, 'response') and e.response is not None:
                    if e.response.status_code == 403:
                        # Already handled above, but catch if raise_for_status is called
                        raise
                raise NetworkError(
                    f"Network error during {operation}: {str(e)}",
                    endpoint=url
                )
        
        # Use IPv4-only context if enabled
        if should_use_ipv4_only():
            with ipv4_only_context():
                return do_request()
        else:
            return do_request()

    def list_role_assignments(
        self, 
        principal_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List Azure AD role assignments for the user.
        Uses ARM API with asTarget() filter instead of Graph API to avoid permission issues.

        Args:
            principal_id: Principal ID (user object ID) - not used with asTarget() filter
            limit: Maximum number of results to return

        Returns:
            List of role assignments
        """
        # Use ARM API with asTarget() filter - this matches what Azure Portal uses
        # and works with standard Azure CLI permissions without requiring Graph API permissions
        url = f"{self.ARM_API_BASE}/providers/Microsoft.Authorization/roleEligibilityScheduleInstances"
        params = {
            "api-version": "2020-10-01",
            "$filter": "asTarget()"  # Gets roles for the current authenticated user
        }

        headers = self._get_headers("https://management.azure.com/.default")
        
        all_results = []
        while True:
            data = self._make_request(
                "GET", url, headers, params,
                operation="list role assignments"
            )
            
            values = data.get("value", [])
            all_results.extend(values)
            
            if self.verbose:
                print(f"[DEBUG] Retrieved {len(values)} roles (total: {len(all_results)})")
            
            # Check if we've hit the limit
            if limit and len(all_results) >= limit:
                all_results = all_results[:limit]
                break
            
            # Handle pagination
            next_link = data.get("nextLink")
            if not next_link:
                break
            
            url = next_link
            params = {}  # nextLink already includes params
        
        return all_results

    def list_resource_role_assignments(
        self, 
        scope: str, 
        principal_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List Azure resource role assignments.

        Args:
            scope: Resource scope (e.g., subscription, resource group)
            principal_id: Principal ID (user object ID)
            limit: Maximum number of results to return

        Returns:
            List of role assignments
        """
        if principal_id is None:
            principal_id = self.auth.get_user_object_id()

        url = f"{self.ARM_API_BASE}/{scope}/providers/Microsoft.Authorization/roleEligibilitySchedules"
        params = {"api-version": "2020-10-01", "$filter": f"principalId eq '{principal_id}'"}

        headers = self._get_headers("https://management.azure.com/.default")
        
        all_results = []
        while True:
            data = self._make_request(
                "GET", url, headers, params,
                operation=f"list resource role assignments for scope {scope}"
            )
            
            values = data.get("value", [])
            all_results.extend(values)
            
            if self.verbose:
                print(f"[DEBUG] Retrieved {len(values)} resource roles (total: {len(all_results)})")
            
            # Check if we've hit the limit
            if limit and len(all_results) >= limit:
                all_results = all_results[:limit]
                break
            
            # Handle pagination
            next_link = data.get("nextLink")
            if not next_link:
                break
            
            url = next_link
            params = {}  # nextLink already includes params
        
        return all_results

    def request_role_activation(
        self,
        role_definition_id: str,
        principal_id: Optional[str] = None,
        duration: str = "PT8H",
        justification: str = "Requested via az-pim-cli",
        ticket_number: Optional[str] = None,
        ticket_system: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Request Azure AD role activation.

        Args:
            role_definition_id: Role definition ID
            principal_id: Principal ID (user object ID)
            duration: Duration in ISO 8601 format (e.g., PT8H for 8 hours)
            justification: Justification for activation
            ticket_number: Optional ticket number
            ticket_system: Optional ticket system

        Returns:
            Activation request response
        """
        if principal_id is None:
            principal_id = self.auth.get_user_object_id()

        url = f"{self.GRAPH_API_BETA}/roleManagement/directory/roleAssignmentScheduleRequests"

        payload = {
            "action": "selfActivate",
            "principalId": principal_id,
            "roleDefinitionId": role_definition_id,
            "directoryScopeId": "/",
            "justification": justification,
            "scheduleInfo": {
                "startDateTime": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "expiration": {"type": "afterDuration", "duration": duration},
            },
        }

        if ticket_number and ticket_system:
            payload["ticketInfo"] = {"ticketNumber": ticket_number, "ticketSystem": ticket_system}

        headers = self._get_headers()
        
        return self._make_request(
            "POST", url, headers, json_data=payload,
            operation="activate Azure AD role"
        )

    def request_resource_role_activation(
        self,
        scope: str,
        role_definition_id: str,
        principal_id: Optional[str] = None,
        duration: str = "PT8H",
        justification: str = "Requested via az-pim-cli",
        ticket_number: Optional[str] = None,
        ticket_system: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Request Azure resource role activation.

        Args:
            scope: Resource scope
            role_definition_id: Role definition ID
            principal_id: Principal ID (user object ID)
            duration: Duration in ISO 8601 format
            justification: Justification for activation
            ticket_number: Optional ticket number
            ticket_system: Optional ticket system

        Returns:
            Activation request response
        """
        if principal_id is None:
            principal_id = self.auth.get_user_object_id()

        url = f"{self.ARM_API_BASE}/{scope}/providers/Microsoft.Authorization/roleAssignmentScheduleRequests"

        payload = {
            "properties": {
                "principalId": principal_id,
                "roleDefinitionId": role_definition_id,
                "requestType": "SelfActivate",
                "justification": justification,
                "scheduleInfo": {
                    "startDateTime": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "expiration": {"type": "AfterDuration", "duration": duration},
                },
            }
        }

        if ticket_number and ticket_system:
            payload["properties"]["ticketInfo"] = {
                "ticketNumber": ticket_number,
                "ticketSystem": ticket_system,
            }

        params = {"api-version": "2020-10-01"}
        headers = self._get_headers("https://management.azure.com/.default")
        
        return self._make_request(
            "PUT", url, headers, params, json_data=payload,
            operation=f"activate resource role on scope {scope}"
        )

    def list_pending_approvals(self, principal_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List pending approval requests for Azure AD roles.

        Args:
            principal_id: Principal ID (user object ID)

        Returns:
            List of pending approvals
        """
        if principal_id is None:
            principal_id = self.auth.get_user_object_id()

        url = f"{self.GRAPH_API_BETA}/roleManagement/directory/roleAssignmentScheduleRequests"
        params = {"$filter": "status eq 'PendingApproval'"}

        headers = self._get_headers()
        data = self._make_request(
            "GET", url, headers, params,
            operation="list pending approvals"
        )

        return data.get("value", [])

    def approve_request(
        self, request_id: str, justification: str = "Approved via az-pim-cli"
    ) -> Dict[str, Any]:
        """
        Approve a role assignment request.

        Args:
            request_id: Request ID to approve
            justification: Justification for approval

        Returns:
            Approval response
        """
        url = f"{self.GRAPH_API_BETA}/roleManagement/directory/roleAssignmentScheduleRequests/{request_id}/approve"

        payload = {"justification": justification}

        headers = self._get_headers()
        
        return self._make_request(
            "POST", url, headers, json_data=payload,
            operation=f"approve request {request_id}"
        )

    def list_activation_history(
        self, principal_id: Optional[str] = None, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        List activation history for Azure AD roles.

        Args:
            principal_id: Principal ID (user object ID)
            days: Number of days to look back

        Returns:
            List of activations
        """
        if principal_id is None:
            principal_id = self.auth.get_user_object_id()

        url = f"{self.GRAPH_API_BETA}/roleManagement/directory/roleAssignmentScheduleInstances"
        params = {"$filter": f"principalId eq '{principal_id}'", "$expand": "roleDefinition"}

        headers = self._get_headers()
        data = self._make_request(
            "GET", url, headers, params,
            operation="list activation history"
        )

        return data.get("value", [])
