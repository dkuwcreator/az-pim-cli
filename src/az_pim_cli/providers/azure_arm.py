"""Azure Resource Manager (ARM) provider for Azure resource roles.

This module handles all ARM API calls for Azure resource PIM operations.
Uses the modern ARM PIM APIs under Microsoft.Authorization.

API Reference:
- https://learn.microsoft.com/en-us/rest/api/authorization/role-assignment-schedule-requests
- https://learn.microsoft.com/en-us/rest/api/authorization/role-eligibility-schedule-instances

Required Permissions:
- See docs/PERMISSIONS.md for detailed permission requirements
"""

import uuid
from datetime import datetime, timezone
from typing import Any

import requests

from az_pim_cli.auth import AzureAuth, ipv4_only_context, should_use_ipv4_only
from az_pim_cli.exceptions import NetworkError, ParsingError, PermissionError


class AzureARMProvider:
    """Provider for Azure Resource Manager PIM APIs (Azure resource roles)."""

    ARM_API_BASE = "https://management.azure.com"
    API_VERSION = "2020-10-01"

    def __init__(self, auth: AzureAuth | None = None, verbose: bool = False) -> None:
        """
        Initialize Azure ARM provider.

        Args:
            auth: Azure authentication instance
            verbose: Enable verbose logging
        """
        self.auth = auth or AzureAuth()
        self.verbose = verbose

        if self.verbose:
            print("[DEBUG] AzureARMProvider initialized")

    def _get_headers(self) -> dict[str, str]:
        """
        Get headers with authorization token for ARM API.

        Returns:
            Headers dictionary
        """
        token = self.auth.get_token("https://management.azure.com/.default")
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
        operation: str = "ARM API request",
    ) -> dict[str, Any]:
        """
        Make an HTTP request to ARM API with error handling.

        Args:
            method: HTTP method (GET, PUT)
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
                elif method == "PUT":
                    response = requests.put(
                        url, headers=headers, params=params, json=json_data, timeout=30
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                if response.status_code == 403:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get("error", {}).get("message", "Insufficient permissions")
                    raise PermissionError(
                        message=f"Permission denied for {operation}",
                        endpoint=url,
                        principal_id=self.auth.get_user_object_id(),
                        required_permissions=[
                            "Microsoft.Authorization/roleEligibilityScheduleInstances/read",
                            "Microsoft.Authorization/roleAssignmentScheduleRequests/write",
                        ],
                        detail=error_msg,
                    )

                response.raise_for_status()
                return response.json()

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
        self, scope: str, principal_id: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        List eligible Azure resource roles at a scope.

        API: GET {scope}/providers/Microsoft.Authorization/roleEligibilityScheduleInstances
        Reference: https://learn.microsoft.com/en-us/rest/api/authorization/role-eligibility-schedule-instances/list-for-scope

        Args:
            scope: Resource scope (subscription, resource group, or resource)
            principal_id: User object ID (defaults to current user with asTarget filter)
            limit: Maximum number of results

        Returns:
            List of role eligibility instances
        """
        url = f"{self.ARM_API_BASE}/{scope}/providers/Microsoft.Authorization/roleEligibilityScheduleInstances"

        if principal_id is None:
            params = {
                "api-version": self.API_VERSION,
                "$filter": "asTarget()",
            }
        else:
            params = {
                "api-version": self.API_VERSION,
                "$filter": f"principalId eq '{principal_id}'",
            }

        all_results = []
        while True:
            data = self._make_request(
                "GET", url, params, operation=f"list eligible Azure resource roles at {scope}"
            )

            values = data.get("value", [])
            all_results.extend(values)

            if self.verbose:
                print(f"[DEBUG] Retrieved {len(values)} resource roles (total: {len(all_results)})")

            if limit and len(all_results) >= limit:
                all_results = all_results[:limit]
                break

            next_link = data.get("nextLink")
            if not next_link:
                break

            url = next_link
            params = {}

        return all_results

    def activate_role(
        self,
        scope: str,
        role_definition_id: str,
        principal_id: str | None = None,
        duration: str = "PT8H",
        justification: str = "Requested via az-pim-cli",
        ticket_number: str | None = None,
        ticket_system: str | None = None,
    ) -> dict[str, Any]:
        """
        Activate an Azure resource role (self-activate).

        API: PUT {scope}/providers/Microsoft.Authorization/roleAssignmentScheduleRequests/{guid}
        Reference: https://learn.microsoft.com/en-us/rest/api/authorization/role-assignment-schedule-requests/create

        Args:
            scope: Resource scope
            role_definition_id: Full role definition ID
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

        request_name = str(uuid.uuid4())
        url = f"{self.ARM_API_BASE}/{scope}/providers/Microsoft.Authorization/roleAssignmentScheduleRequests/{request_name}"

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

        params = {"api-version": self.API_VERSION}

        return self._make_request(
            "PUT", url, params, json_data=payload, operation=f"activate Azure resource role at {scope}"
        )

    def list_assignment_requests(
        self, scope: str, principal_id: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        List role assignment requests (history) at a scope.

        API: GET {scope}/providers/Microsoft.Authorization/roleAssignmentScheduleRequests
        Reference: https://learn.microsoft.com/en-us/rest/api/authorization/role-assignment-schedule-requests/list-for-scope

        Args:
            scope: Resource scope
            principal_id: User object ID (defaults to current user)
            limit: Maximum number of results

        Returns:
            List of assignment requests
        """
        url = f"{self.ARM_API_BASE}/{scope}/providers/Microsoft.Authorization/roleAssignmentScheduleRequests"

        if principal_id is None:
            params = {
                "api-version": self.API_VERSION,
                "$filter": "asTarget()",
            }
        else:
            params = {
                "api-version": self.API_VERSION,
                "$filter": f"principalId eq '{principal_id}'",
            }

        all_results = []
        while True:
            data = self._make_request(
                "GET", url, params, operation=f"list Azure resource role requests at {scope}"
            )

            values = data.get("value", [])
            all_results.extend(values)

            if limit and len(all_results) >= limit:
                all_results = all_results[:limit]
                break

            next_link = data.get("nextLink")
            if not next_link:
                break

            url = next_link
            params = {}

        return all_results

    def list_active_assignments(
        self, scope: str, principal_id: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        List active Azure resource role assignments at a scope.

        API: GET {scope}/providers/Microsoft.Authorization/roleAssignmentScheduleInstances
        Reference: https://learn.microsoft.com/en-us/rest/api/authorization/role-assignment-schedule-instances/list-for-scope

        Args:
            scope: Resource scope
            principal_id: User object ID (defaults to current user)
            limit: Maximum number of results

        Returns:
            List of active role assignments
        """
        url = f"{self.ARM_API_BASE}/{scope}/providers/Microsoft.Authorization/roleAssignmentScheduleInstances"

        if principal_id is None:
            params = {
                "api-version": self.API_VERSION,
                "$filter": "asTarget()",
            }
        else:
            params = {
                "api-version": self.API_VERSION,
                "$filter": f"principalId eq '{principal_id}'",
            }

        all_results = []
        while True:
            data = self._make_request(
                "GET", url, params, operation=f"list active Azure resource roles at {scope}"
            )

            values = data.get("value", [])
            all_results.extend(values)

            if limit and len(all_results) >= limit:
                all_results = all_results[:limit]
                break

            next_link = data.get("nextLink")
            if not next_link:
                break

            url = next_link
            params = {}

        return all_results
