"""Tests for response normalization."""

from az_pim_cli.models import (
    normalize_arm_role,
    normalize_graph_role,
    normalize_roles,
    RoleSource,
    NormalizedRole,
)


def test_normalize_arm_role():
    """Test normalizing an ARM API response."""
    arm_response = {
        "id": "/providers/Microsoft.Authorization/roleEligibilityScheduleInstances/test-id",
        "properties": {
            "roleDefinitionId": "/providers/Microsoft.Authorization/roleDefinitions/role-123",
            "principalId": "user-456",
            "scope": "/subscriptions/sub-789",
            "status": "Active",
            "expandedProperties": {
                "roleDefinition": {
                    "displayName": "Contributor",
                    "id": "/providers/Microsoft.Authorization/roleDefinitions/role-123",
                },
                "scope": {
                    "displayName": "Test Subscription",
                    "id": "/subscriptions/sub-789",
                    "type": "subscription",
                },
            },
        },
    }

    normalized = normalize_arm_role(arm_response)

    assert normalized.name == "Contributor"
    assert normalized.id == "/providers/Microsoft.Authorization/roleDefinitions/role-123"
    assert normalized.status == "Active"
    assert normalized.scope == "/subscriptions/sub-789"
    assert normalized.source == RoleSource.ARM


def test_normalize_graph_role():
    """Test normalizing a Graph API response."""
    graph_response = {
        "id": "test-id",
        "roleDefinitionId": "role-123",
        "principalId": "user-456",
        "directoryScopeId": "/",
        "status": "Provisioned",
        "roleDefinition": {"displayName": "Global Administrator", "id": "role-123"},
    }

    normalized = normalize_graph_role(graph_response)

    assert normalized.name == "Global Administrator"
    assert normalized.id == "role-123"
    assert normalized.status == "Provisioned"
    assert normalized.scope == "/"
    assert normalized.source == RoleSource.GRAPH


def test_normalize_roles_arm():
    """Test normalizing a list of ARM responses."""
    arm_responses = [
        {
            "properties": {
                "roleDefinitionId": "role-1",
                "status": "Active",
                "scope": "/",
                "expandedProperties": {"roleDefinition": {"displayName": "Role 1"}},
            }
        },
        {
            "properties": {
                "roleDefinitionId": "role-2",
                "status": "Active",
                "scope": "/",
                "expandedProperties": {"roleDefinition": {"displayName": "Role 2"}},
            }
        },
    ]

    normalized = normalize_roles(arm_responses, RoleSource.ARM)

    assert len(normalized) == 2
    assert normalized[0].name == "Role 1"
    assert normalized[1].name == "Role 2"
    assert all(role.source == RoleSource.ARM for role in normalized)


def test_normalized_role_to_dict():
    """Test converting normalized role to dictionary."""
    role = NormalizedRole(
        name="Test Role",
        id="role-123",
        status="Active",
        scope="/subscriptions/sub-789",
        source=RoleSource.ARM,
    )

    role_dict = role.to_dict()

    assert role_dict["name"] == "Test Role"
    assert role_dict["id"] == "role-123"
    assert role_dict["status"] == "Active"
    assert role_dict["scope"] == "/subscriptions/sub-789"
    assert role_dict["source"] == "ARM"


def test_get_short_scope():
    """Test getting shortened scope for display."""
    # Test subscription scope
    role1 = NormalizedRole(
        name="Test",
        id="id",
        status="Active",
        scope="/subscriptions/12345678-1234-1234-1234-123456789abc",
    )
    assert "sub:12345678..." in role1.get_short_scope()

    # Test resource group scope
    role2 = NormalizedRole(
        name="Test",
        id="id",
        status="Active",
        scope="/subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/my-rg",
    )
    short = role2.get_short_scope()
    assert "sub:12345678..." in short
    assert "rg:my-rg" in short

    # Test root scope
    role3 = NormalizedRole(name="Test", id="id", status="Active", scope="/")
    assert role3.get_short_scope() == "/"

    # Test empty scope
    role4 = NormalizedRole(name="Test", id="id", status="Active", scope="")
    assert role4.get_short_scope() == "/"


def test_normalize_arm_role_with_missing_fields():
    """Test normalizing ARM response with missing fields."""
    arm_response = {"properties": {}}

    normalized = normalize_arm_role(arm_response)

    assert normalized.name == "Unknown"
    assert normalized.id == ""
    assert normalized.status == "Active"


def test_normalize_graph_role_with_missing_fields():
    """Test normalizing Graph response with missing fields."""
    graph_response = {}

    normalized = normalize_graph_role(graph_response)

    assert normalized.name == "Unknown"
    assert normalized.id == ""
    assert normalized.status == "Provisioned"
    assert normalized.scope == "/"
