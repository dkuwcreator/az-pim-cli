"""Tests for response normalization."""

from az_pim_cli.models import (
    normalize_arm_role,
    normalize_graph_role,
    normalize_roles,
    RoleSource,
    NormalizedRole,
    alias_to_normalized_role,
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
    assert normalized.resource_name == "Test Subscription"
    assert normalized.resource_type == "subscription"


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


def test_normalize_arm_role_with_portal_fields():
    """Test normalizing ARM response with all portal fields."""
    arm_response = {
        "id": "/providers/Microsoft.Authorization/roleEligibilityScheduleInstances/test-id",
        "properties": {
            "roleDefinitionId": "/providers/Microsoft.Authorization/roleDefinitions/role-123",
            "principalId": "user-456",
            "scope": "/subscriptions/sub-789",
            "status": "Active",
            "memberType": "Direct",
            "condition": "@Resource[Microsoft.Storage/storageAccounts/blobServices/containers:name] StringEquals 'container1'",
            "endDateTime": "2024-12-31T23:59:59Z",
            "expandedProperties": {
                "roleDefinition": {
                    "displayName": "Storage Blob Data Contributor",
                    "id": "/providers/Microsoft.Authorization/roleDefinitions/role-123",
                },
                "scope": {
                    "displayName": "My Storage Account",
                    "id": "/subscriptions/sub-789/resourceGroups/rg-test/providers/Microsoft.Storage/storageAccounts/mystore",
                    "type": "Microsoft.Storage/storageAccounts",
                },
            },
        },
    }

    normalized = normalize_arm_role(arm_response)

    assert normalized.name == "Storage Blob Data Contributor"
    assert normalized.resource_name == "My Storage Account"
    assert normalized.resource_type == "Microsoft.Storage/storageAccounts"
    assert normalized.membership_type == "Direct"
    assert normalized.condition == "@Resource[Microsoft.Storage/storageAccounts/blobServices/containers:name] StringEquals 'container1'"
    assert normalized.end_time == "2024-12-31T23:59:59Z"


def test_alias_to_normalized_role():
    """Test converting an alias to a NormalizedRole."""
    alias_name = "prod-admin"
    alias_config = {
        "role": "Owner",
        "duration": "PT8H",
        "justification": "Production deployment",
        "scope": "subscription",
        "subscription": "12345678-1234-1234-1234-123456789abc",
        "resource": "Production Subscription",
        "resource_type": "subscription",
        "membership": "Eligible",
    }

    normalized = alias_to_normalized_role(alias_name, alias_config)

    assert normalized.name == "Owner"
    assert normalized.is_alias is True
    assert normalized.alias_name == "prod-admin"
    assert normalized.status == "Eligible"
    assert normalized.end_time == "Duration: 8h"
    assert normalized.resource_name == "Production Subscription"
    assert normalized.resource_type == "subscription"
    assert normalized.scope == "subscriptions/12345678-1234-1234-1234-123456789abc"


def test_alias_to_normalized_role_minimal():
    """Test converting a minimal alias to a NormalizedRole."""
    alias_name = "minimal-alias"
    alias_config = {
        "role": "Reader",
    }

    normalized = alias_to_normalized_role(alias_name, alias_config)

    assert normalized.name == "Reader"
    assert normalized.is_alias is True
    assert normalized.alias_name == "minimal-alias"
    assert normalized.status == "Eligible"
    assert normalized.end_time is None
    assert normalized.scope == ""
