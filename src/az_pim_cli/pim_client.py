"""Azure PIM API client."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

from az_pim_cli.auth import AzureAuth


class PIMClient:
    """Client for interacting with Azure PIM APIs."""

    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
    GRAPH_API_BETA = "https://graph.microsoft.com/beta"
    ARM_API_BASE = "https://management.azure.com"

    def __init__(self, auth: Optional[AzureAuth] = None) -> None:
        """
        Initialize PIM client.

        Args:
            auth: Azure authentication instance
        """
        self.auth = auth or AzureAuth()

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

    def list_role_assignments(self, principal_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List Azure AD role assignments for the user.
        Uses ARM API with asTarget() filter instead of Graph API to avoid permission issues.

        Args:
            principal_id: Principal ID (user object ID) - not used with asTarget() filter

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
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        return data.get("value", [])

    def list_resource_role_assignments(
        self, scope: str, principal_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List Azure resource role assignments.

        Args:
            scope: Resource scope (e.g., subscription, resource group)
            principal_id: Principal ID (user object ID)

        Returns:
            List of role assignments
        """
        if principal_id is None:
            principal_id = self.auth.get_user_object_id()

        url = f"{self.ARM_API_BASE}/{scope}/providers/Microsoft.Authorization/roleEligibilitySchedules"
        params = {"api-version": "2020-10-01", "$filter": f"principalId eq '{principal_id}'"}

        headers = self._get_headers("https://management.azure.com/.default")
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        return data.get("value", [])

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
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        return response.json()

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
        response = requests.put(url, headers=headers, params=params, json=payload)
        response.raise_for_status()

        return response.json()

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
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
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
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        return response.json()

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
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        return data.get("value", [])
