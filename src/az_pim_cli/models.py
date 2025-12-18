"""Response normalization for Azure PIM CLI.

This module provides a mapping layer to normalize ARM and Graph API responses
into a common role model, keeping UI logic stable when switching backends.
"""

from typing import Any, Dict, List, Optional
from enum import Enum


class RoleSource(Enum):
    """Source of role data."""

    ARM = "ARM"
    GRAPH = "Graph"


class NormalizedRole:
    """Normalized role model that works with both ARM and Graph responses."""

    def __init__(
        self,
        name: str,
        id: str,
        status: str,
        scope: str = "",
        source: RoleSource = RoleSource.ARM,
        raw_data: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.id = id
        self.status = status
        self.scope = scope
        self.source = source
        self.raw_data = raw_data or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "id": self.id,
            "status": self.status,
            "scope": self.scope,
            "source": self.source.value,
        }

    def get_short_scope(self) -> str:
        """Get a shortened version of the scope for display."""
        if not self.scope:
            return "/"

        # Extract key parts of scope path
        parts = self.scope.split("/")
        if "subscriptions" in parts:
            sub_idx = parts.index("subscriptions")
            if sub_idx + 1 < len(parts):
                sub_id = parts[sub_idx + 1][:8]  # First 8 chars of subscription ID
                if "resourceGroups" in parts:
                    rg_idx = parts.index("resourceGroups")
                    if rg_idx + 1 < len(parts):
                        return f"sub:{sub_id}.../rg:{parts[rg_idx + 1]}"
                return f"sub:{sub_id}..."
        return self.scope[:30] + "..." if len(self.scope) > 30 else self.scope


def normalize_arm_role(arm_response: Dict[str, Any]) -> NormalizedRole:
    """
    Normalize an ARM API role response.

    ARM response format (roleEligibilityScheduleInstance):
    {
        "id": "...",
        "properties": {
            "roleDefinitionId": "...",
            "principalId": "...",
            "scope": "...",
            "status": "...",
            "expandedProperties": {
                "roleDefinition": {
                    "displayName": "...",
                    "id": "..."
                },
                "scope": {
                    "displayName": "...",
                    "id": "...",
                    "type": "..."
                }
            }
        }
    }
    """
    props = arm_response.get("properties", {})
    expanded = props.get("expandedProperties", {})
    role_def = expanded.get("roleDefinition", {})
    scope_info = expanded.get("scope", {})

    name = role_def.get("displayName", "Unknown")
    role_id = props.get("roleDefinitionId", "")
    status = props.get("status", "Active")
    scope = props.get("scope", scope_info.get("id", ""))

    return NormalizedRole(
        name=name,
        id=role_id,
        status=status,
        scope=scope,
        source=RoleSource.ARM,
        raw_data=arm_response,
    )


def normalize_graph_role(graph_response: Dict[str, Any]) -> NormalizedRole:
    """
    Normalize a Graph API role response.

    Graph response format (roleEligibilitySchedule):
    {
        "id": "...",
        "roleDefinitionId": "...",
        "principalId": "...",
        "directoryScopeId": "...",
        "status": "...",
        "roleDefinition": {
            "displayName": "...",
            "id": "..."
        }
    }
    """
    role_def = graph_response.get("roleDefinition", {})

    name = role_def.get("displayName", "Unknown")
    role_id = graph_response.get("roleDefinitionId", "")
    status = graph_response.get("status", "Provisioned")
    scope = graph_response.get("directoryScopeId", "/")

    return NormalizedRole(
        name=name,
        id=role_id,
        status=status,
        scope=scope,
        source=RoleSource.GRAPH,
        raw_data=graph_response,
    )


def normalize_roles(
    responses: List[Dict[str, Any]], source: RoleSource = RoleSource.ARM
) -> List[NormalizedRole]:
    """
    Normalize a list of role responses based on their source.

    Args:
        responses: List of role responses
        source: Source of the responses (ARM or Graph)

    Returns:
        List of normalized roles
    """
    if source == RoleSource.ARM:
        return [normalize_arm_role(r) for r in responses]
    else:
        return [normalize_graph_role(r) for r in responses]
