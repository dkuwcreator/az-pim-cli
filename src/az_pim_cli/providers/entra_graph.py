"""Microsoft Graph provider for Entra ID (Azure AD) roles.

This module handles all Microsoft Graph API calls for Entra ID PIM operations.
Uses the modern PIM v3 API under /roleManagement/directory/.

API Reference:
- https://learn.microsoft.com/en-us/graph/api/resources/privilegedidentitymanagementv3-overview
- https://learn.microsoft.com/en-us/graph/api/rbacapplication-list-roleassignmentschedulerequests

Required Permissions:
- See docs/PERMISSIONS.md for detailed permission requirements
"""

from datetime import datetime, timezone
from typing import Any

import requests

from az_pim_cli.auth import AzureAuth, ipv4_only_context, should_use_ipv4_only
from az_pim_cli.exceptions import NetworkError, ParsingError, PermissionError


class EntraGraphProvider:
    """Provider for Microsoft Graph PIM APIs (Entra ID roles)."""

    GRAPH_API_V1 = "https://graph.microsoft.com/v1.0"
    GRAPH_API_BETA = "https://graph.microsoft.com/beta"

    def __init__(self, auth: AzureAuth | None = None, verbose: bool = False) -> None:
        """
        Initialize Entra Graph provider.

        Args:
            auth: Azure authentication instance
            verbose: Enable verbose logging
        """
        self.auth = auth or AzureAuth()
        self.verbose = verbose

        if self.verbose:
            print("[DEBUG] EntraGraphProvider initialized")

    def _get_headers(self) -> dict[str, str]:
        """
        Get headers with authorization token for Graph API.

        Returns:
            Headers dictionary
        """
        token = self.auth.get_token("https://graph.microsoft.com/.default")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        operation: str = "Graph API request",
    ) -> dict[str, Any]:
        """
        Make an HTTP request to Graph API with error handling.

        Args:
            method: HTTP method (GET, POST)
            url: Request URL
            params: Query parameters
            json_data: JSON body
            operation: Description for error messages

        Returns:
            Response JSON data

        Raises:
            NetworkError: For DNS, timeout, and connection errors
            PermissionError: For 403 authorization errors
            ParsingError: For response parsing errors
        """

        def do_request() -> dict[str, Any]:
            try:
                headers = self._get_headers()

                if self.verbose:
                    print(f"[DEBUG] {method} {url}")
                    if params:
                        print(f"[DEBUG] Params: {params}")

                if method == "GET":
                    response = requests.get(url, headers=headers, params=params, timeout=30)
                elif method == "POST":
                    response = requests.post(
                        url, headers=headers, params=params, json=json_data, timeout=30
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                if response.status_code == 403:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get("error", {}).get("message", "Insufficient permissions")
                    raise PermissionError(
                        message=f"Permission denied for {operation}: {error_msg}",
                        endpoint=url,
                        required_permissions="RoleManagement.ReadWrite.Directory or RoleAssignmentSchedule.ReadWrite.Directory",
                    )

                response.raise_for_status()
                return response.json()  # type: ignore[no-any-return]

            except requests.exceptions.Timeout:
                raise NetworkError(
                    f"Request timeout for {operation}",
                    endpoint=url,
                    suggest_ipv4=True,
                )
            except requests.exceptions.ConnectionError as e:
                if "getaddrinfo failed" in str(e) or "Name or service not known" in str(e):
                    raise NetworkError(
                        f"DNS resolution failed for {operation}",
                        endpoint=url,
                        suggest_ipv4=True,
                    )
                raise NetworkError(f"Connection error for {operation}: {e}", endpoint=url)
            except requests.exceptions.RequestException as e:
                if hasattr(e, "response") and e.response is not None:
                    if e.response.status_code == 403:
                        raise  # Already handled above
                raise NetworkError(f"Request failed for {operation}: {e}", endpoint=url)
            except (KeyError, ValueError) as e:
                raise ParsingError(f"Failed to parse response for {operation}: {e}")

        if should_use_ipv4_only():
            with ipv4_only_context():
                return do_request()
        else:
            return do_request()

    def list_eligible_roles(
        self, principal_id: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        List eligible Entra ID roles for a user.

        API: GET /roleManagement/directory/roleEligibilityScheduleInstances
        Reference: https://learn.microsoft.com/en-us/graph/api/rbacapplication-list-roleeligibilityscheduleinstances

        Args:
            principal_id: User object ID (defaults to current user)
            limit: Maximum number of results

        Returns:
            List of role eligibility instances
        """
        if principal_id is None:
            principal_id = self.auth.get_user_object_id()

        url = f"{self.GRAPH_API_BETA}/roleManagement/directory/roleEligibilityScheduleInstances"
        params = {
            "$filter": f"principalId eq '{principal_id}'",
            "$expand": "roleDefinition",
        }

        all_results = []
        while True:
            data = self._make_request(
                "GET", url, params, operation="list eligible Entra roles"
            )

            values = data.get("value", [])
            all_results.extend(values)

            if self.verbose:
                print(f"[DEBUG] Retrieved {len(values)} Entra roles (total: {len(all_results)})")

            if limit and len(all_results) >= limit:
                all_results = all_results[:limit]
                break

            next_link = data.get("@odata.nextLink")
            if not next_link:
                break

            url = next_link
            params = {}

        return all_results

    def activate_role(
        self,
        role_definition_id: str,
        principal_id: str | None = None,
        duration: str = "PT8H",
        justification: str = "Requested via az-pim-cli",
        ticket_number: str | None = None,
        ticket_system: str | None = None,
    ) -> dict[str, Any]:
        """
        Activate an Entra ID role (self-activate).

        API: POST /roleManagement/directory/roleAssignmentScheduleRequests
        Reference: https://learn.microsoft.com/en-us/graph/api/rbacapplication-post-roleassignmentschedulerequests

        Args:
            role_definition_id: Role definition ID (GUID)
            principal_id: User object ID (defaults to current user)
            duration: ISO 8601 duration (e.g., PT8H)
            justification: Reason for activation
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

        return self._make_request(
            "POST", url, json_data=payload, operation="activate Entra role"
        )

    def list_assignment_requests(
        self, principal_id: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        List role assignment requests (history).

        API: GET /roleManagement/directory/roleAssignmentScheduleRequests
        Reference: https://learn.microsoft.com/en-us/graph/api/rbacapplication-list-roleassignmentschedulerequests

        Args:
            principal_id: User object ID (defaults to current user)
            limit: Maximum number of results

        Returns:
            List of assignment requests
        """
        if principal_id is None:
            principal_id = self.auth.get_user_object_id()

        url = f"{self.GRAPH_API_BETA}/roleManagement/directory/roleAssignmentScheduleRequests"
        params = {
            "$filter": f"principalId eq '{principal_id}'",
            "$orderby": "createdDateTime desc",
        }

        all_results = []
        while True:
            data = self._make_request(
                "GET", url, params, operation="list Entra role assignment requests"
            )

            values = data.get("value", [])
            all_results.extend(values)

            if limit and len(all_results) >= limit:
                all_results = all_results[:limit]
                break

            next_link = data.get("@odata.nextLink")
            if not next_link:
                break

            url = next_link
            params = {}

        return all_results

    def list_pending_approvals(self) -> list[dict[str, Any]]:
        """
        List pending approval requests where current user is an approver.

        API: GET /roleManagement/directory/roleAssignmentScheduleRequests/filterByCurrentUser(on='approver')
        Reference: https://learn.microsoft.com/en-us/entra/id-governance/privileged-identity-management/pim-approval-workflow

        Returns:
            List of pending approval requests
        """
        url = f"{self.GRAPH_API_BETA}/roleManagement/directory/roleAssignmentScheduleRequests/filterByCurrentUser(on='approver')"
        params = {"$filter": "status eq 'PendingApproval'"}

        data = self._make_request(
            "GET", url, params, operation="list pending Entra role approvals"
        )

        return data.get("value", [])  # type: ignore[no-any-return]

    def approve_request(
        self, request_id: str, justification: str = "Approved via az-pim-cli"
    ) -> dict[str, Any]:
        """
        Approve a pending role activation request.

        API: POST /roleManagement/directory/roleAssignmentScheduleRequests/{id}/approve
        Reference: https://learn.microsoft.com/en-us/graph/api/unifiedroleassignmentschedulerequest-approve

        Args:
            request_id: Request ID to approve
            justification: Approval reason

        Returns:
            Approval response
        """
        url = f"{self.GRAPH_API_BETA}/roleManagement/directory/roleAssignmentScheduleRequests/{request_id}/approve"
        payload = {"justification": justification}

        return self._make_request(
            "POST", url, json_data=payload, operation="approve Entra role request"
        )

    def list_active_assignments(
        self, principal_id: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        List active Entra ID role assignments.

        API: GET /roleManagement/directory/roleAssignmentScheduleInstances
        Reference: https://learn.microsoft.com/en-us/graph/api/rbacapplication-list-roleassignmentscheduleinstances

        Args:
            principal_id: User object ID (defaults to current user)
            limit: Maximum number of results

        Returns:
            List of active role assignments
        """
        if principal_id is None:
            principal_id = self.auth.get_user_object_id()

        url = f"{self.GRAPH_API_BETA}/roleManagement/directory/roleAssignmentScheduleInstances"
        params = {
            "$filter": f"principalId eq '{principal_id}'",
            "$expand": "roleDefinition",
        }

        all_results = []
        while True:
            data = self._make_request(
                "GET", url, params, operation="list active Entra role assignments"
            )

            values = data.get("value", [])
            all_results.extend(values)

            if limit and len(all_results) >= limit:
                all_results = all_results[:limit]
                break

            next_link = data.get("@odata.nextLink")
            if not next_link:
                break

            url = next_link
            params = {}

        return all_results
