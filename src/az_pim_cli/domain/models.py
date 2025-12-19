"""Response normalization for Azure PIM CLI.

This module provides a mapping layer to normalize ARM and Graph API responses
into a common role model, keeping UI logic stable when switching backends.
"""

from enum import Enum
from typing import Any

# Constants
SUBSCRIPTION_ID_DISPLAY_LENGTH = 8  # Number of characters to show from subscription IDs


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
        raw_data: dict[str, Any] | None = None,
        resource_name: str | None = None,
        resource_type: str | None = None,
        membership_type: str | None = None,
        condition: str | None = None,
        end_time: str | None = None,
        is_alias: bool = False,
        alias_name: str | None = None,
    ):
        self.name = name
        self.id = id
        self.status = status
        self.scope = scope
        self.source = source
        self.raw_data = raw_data or {}
        self.resource_name = resource_name
        self.resource_type = resource_type
        self.membership_type = membership_type
        self.condition = condition
        self.end_time = end_time
        self.is_alias = is_alias
        self.alias_name = alias_name

    def to_dict(self) -> dict[str, Any]:
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
                sub_id = parts[sub_idx + 1][:SUBSCRIPTION_ID_DISPLAY_LENGTH]
                if "resourceGroups" in parts:
                    rg_idx = parts.index("resourceGroups")
                    if rg_idx + 1 < len(parts):
                        return f"sub:{sub_id}.../rg:{parts[rg_idx + 1]}"
                return f"sub:{sub_id}..."
        return self.scope[:30] + "..." if len(self.scope) > 30 else self.scope


def normalize_arm_role(arm_response: dict[str, Any]) -> NormalizedRole:
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
            "memberType": "...",
            "condition": "...",
            "endDateTime": "...",
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

    # Extract portal-equivalent fields
    resource_name = scope_info.get("displayName")
    resource_type = scope_info.get("type")
    membership_type = props.get("memberType")
    condition = props.get("condition")
    end_time = props.get("endDateTime")

    return NormalizedRole(
        name=name,
        id=role_id,
        status=status,
        scope=scope,
        source=RoleSource.ARM,
        raw_data=arm_response,
        resource_name=resource_name,
        resource_type=resource_type,
        membership_type=membership_type,
        condition=condition,
        end_time=end_time,
    )


def normalize_graph_role(graph_response: dict[str, Any]) -> NormalizedRole:
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
    responses: list[dict[str, Any]], source: RoleSource = RoleSource.ARM
) -> list[NormalizedRole]:
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


def alias_to_normalized_role(alias_name: str, alias_config: dict[str, Any]) -> NormalizedRole:
    """
    Convert an alias configuration to a NormalizedRole object.

    Args:
        alias_name: Name of the alias
        alias_config: Alias configuration dictionary

    Returns:
        NormalizedRole object representing the alias
    """
    role_name = alias_config.get("role", alias_name)
    role_id = alias_config.get("role", "")

    # For display purposes, show as "Eligible" for aliases
    status = "Eligible"

    # Build scope from alias config
    scope = ""
    if alias_config.get("scope") == "subscription":
        subscription = alias_config.get("subscription", "")
        if subscription:
            scope = f"subscriptions/{subscription}"
            if alias_config.get("resource_group"):
                scope += f"/resourceGroups/{alias_config['resource_group']}"
    elif alias_config.get("scope") == "directory":
        scope = "/"

    # Extract other fields
    resource_name = alias_config.get("resource")
    resource_type = alias_config.get("resource_type")
    membership_type = alias_config.get("membership")
    condition = alias_config.get("condition")

    # Convert duration to end_time format for display
    end_time = None
    if alias_config.get("duration"):
        duration_str = alias_config["duration"]
        # Extract hours from PT format
        if duration_str.startswith("PT") and "H" in duration_str:
            hours = duration_str.replace("PT", "").replace("H", "")
            end_time = f"Duration: {hours}h"

    return NormalizedRole(
        name=role_name,
        id=role_id,
        status=status,
        scope=scope,
        source=RoleSource.ARM,
        resource_name=resource_name,
        resource_type=resource_type,
        membership_type=membership_type,
        condition=condition,
        end_time=end_time,
        is_alias=True,
        alias_name=alias_name,
    )
