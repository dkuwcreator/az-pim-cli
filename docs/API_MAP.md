# API Endpoint Mapping

This document maps each CLI command to the exact Azure API endpoints it uses. This ensures clear separation between Microsoft Graph PIM (for Entra/Azure AD roles) and Azure Resource Manager (ARM) PIM (for Azure resource roles).

## API Backend Selection

The CLI supports two backends:

- **Microsoft Graph PIM v3** (`/roleManagement/directory/...`) - For Entra ID (Azure AD) roles
- **Azure Resource Manager (ARM)** (`{scope}/providers/Microsoft.Authorization/...`) - For Azure resource roles

> **Important**: The deprecated Graph v2 API (`/beta/privilegedAccess/azureResources`) is NOT used, as it will stop returning data on October 28, 2026.

## Authentication & Identity

### Show Current Identity (whoami)

**Command**: `az-pim whoami`

**Description**: Displays current Azure identity information including tenant ID, user object ID, subscription ID, and authentication mode.

**APIs Used**:
- Token introspection (extracting claims from JWT)
- Azure CLI credential chain
- Subscription context from Azure SDK

**Scope**: 
- `https://graph.microsoft.com/.default` (for token validation)
- `https://management.azure.com/.default` (for subscription info)

**Permissions Required**: None (read-only identity information)

**Reference**: Internal authentication methods

---

### Get Current User Info

**Endpoint**: `GET https://graph.microsoft.com/v1.0/me`

**Scope**: `https://graph.microsoft.com/.default`

**Used by**: All commands (to get principal ID)

**Reference**: https://learn.microsoft.com/en-us/graph/api/user-get

### Get Tenant ID

**Method**: Extract from Azure CLI credentials or token claims

**Used by**: All commands

## Entra ID (Azure AD) Roles - Microsoft Graph

### List Eligible Entra Roles

**Command**: `az-pim list` (default, without `--resource` flag)

**Endpoint**: `GET https://graph.microsoft.com/beta/roleManagement/directory/roleEligibilityScheduleInstances`

**Parameters**:
- `$filter=principalId eq '{user-object-id}'`
- `$expand=roleDefinition`

**Scope**: `https://graph.microsoft.com/.default`

**Permissions Required**: 
- `RoleEligibilitySchedule.Read.Directory` (delegated)
- `RoleManagement.Read.Directory` (delegated)

**Reference**: https://learn.microsoft.com/en-us/graph/api/rbacapplication-list-roleeligibilityscheduleinstances

---

### List Active Entra Roles

**Command**: `az-pim entra active` (future command)

**Endpoint**: `GET https://graph.microsoft.com/beta/roleManagement/directory/roleAssignmentScheduleInstances`

**Parameters**:
- `$filter=principalId eq '{user-object-id}'`
- `$expand=roleDefinition`

**Scope**: `https://graph.microsoft.com/.default`

**Permissions Required**: 
- `RoleAssignmentSchedule.Read.Directory` (delegated)
- `RoleManagement.Read.Directory` (delegated)

**Reference**: https://learn.microsoft.com/en-us/graph/api/rbacapplication-list-roleassignmentscheduleinstances

---

### Activate Entra Role (Self-Activate)

**Command**: `az-pim activate <role>` (for Entra roles)

**Endpoint**: `POST https://graph.microsoft.com/beta/roleManagement/directory/roleAssignmentScheduleRequests`

**Request Body**:
```json
{
  "action": "selfActivate",
  "principalId": "{user-object-id}",
  "roleDefinitionId": "{role-definition-id}",
  "directoryScopeId": "/",
  "justification": "Requested via az-pim-cli",
  "scheduleInfo": {
    "startDateTime": "{iso-timestamp}",
    "expiration": {
      "type": "afterDuration",
      "duration": "PT8H"
    }
  },
  "ticketInfo": {
    "ticketNumber": "{ticket}",
    "ticketSystem": "{system}"
  }
}
```

**Scope**: `https://graph.microsoft.com/.default`

**Permissions Required**: 
- `RoleAssignmentSchedule.ReadWrite.Directory` (delegated)
- `RoleManagement.ReadWrite.Directory` (delegated)

**Reference**: https://learn.microsoft.com/en-us/graph/api/rbacapplication-post-roleassignmentschedulerequests

---

### List Entra Role Assignment Requests

**Command**: `az-pim history` (for Entra roles)

**Endpoint**: `GET https://graph.microsoft.com/beta/roleManagement/directory/roleAssignmentScheduleRequests`

**Parameters**:
- `$filter=principalId eq '{user-object-id}'`
- `$orderby=createdDateTime desc`

**Scope**: `https://graph.microsoft.com/.default`

**Permissions Required**: 
- `RoleAssignmentSchedule.Read.Directory` (delegated)

**Reference**: https://learn.microsoft.com/en-us/graph/api/rbacapplication-list-roleassignmentschedulerequests

---

### List Pending Approvals (Entra Roles)

**Command**: `az-pim pending` or `az-pim entra approvals list` (future)

**Endpoint**: `GET https://graph.microsoft.com/beta/roleManagement/directory/roleAssignmentScheduleRequests/filterByCurrentUser(on='approver')`

**Parameters**:
- `$filter=status eq 'PendingApproval'`

**Scope**: `https://graph.microsoft.com/.default`

**Permissions Required**: 
- `RoleAssignmentSchedule.Read.Directory` (delegated)
- User must be configured as an approver for the role

**Notes**: 
- Uses Graph beta endpoint (no v1.0 equivalent yet)
- 24-hour approval window

**Reference**: https://learn.microsoft.com/en-us/entra/id-governance/privileged-identity-management/pim-approval-workflow

---

### Approve Entra Role Request

**Command**: `az-pim approve <request-id>`

**Endpoint**: `POST https://graph.microsoft.com/beta/roleManagement/directory/roleAssignmentScheduleRequests/{request-id}/approve`

**Request Body**:
```json
{
  "justification": "Approved via az-pim-cli"
}
```

**Scope**: `https://graph.microsoft.com/.default`

**Permissions Required**: 
- `RoleManagement.ReadWrite.Directory` (delegated)
- User must be configured as an approver

**Notes**: Uses Graph beta endpoint only

**Reference**: https://learn.microsoft.com/en-us/graph/api/unifiedroleassignmentschedulerequest-approve

---

## Azure Resource Roles - Azure Resource Manager (ARM)

### List Eligible Resource Roles

**Command**: `az-pim list --resource [--scope <scope>]`

**Endpoint**: `GET https://management.azure.com/{scope}/providers/Microsoft.Authorization/roleEligibilityScheduleInstances`

**Parameters**:
- `api-version=2020-10-01`
- `$filter=asTarget()` (for current user)
- `$filter=principalId eq '{principal-id}'` (for specific user)

**Scope**: `https://management.azure.com/.default`

**Permissions Required**: 
- `Microsoft.Authorization/roleEligibilityScheduleInstances/read` at the specified scope
- Standard Azure RBAC permissions (no Graph permissions needed)

**Notes**: 
- Scope can be: subscription, resource group, or specific resource
- Uses ARM, NOT Graph API

**Reference**: https://learn.microsoft.com/en-us/rest/api/authorization/role-eligibility-schedule-instances/list-for-scope

---

### List Active Resource Role Assignments

**Command**: `az-pim azure active` (future command)

**Endpoint**: `GET https://management.azure.com/{scope}/providers/Microsoft.Authorization/roleAssignmentScheduleInstances`

**Parameters**:
- `api-version=2020-10-01`
- `$filter=asTarget()` or `$filter=principalId eq '{principal-id}'`

**Scope**: `https://management.azure.com/.default`

**Permissions Required**: 
- `Microsoft.Authorization/roleAssignmentScheduleInstances/read`

**Reference**: https://learn.microsoft.com/en-us/rest/api/authorization/role-assignment-schedule-instances/list-for-scope

---

### Activate Resource Role (Self-Activate)

**Command**: `az-pim activate <role> --resource --scope <scope>`

**Endpoint**: `PUT https://management.azure.com/{scope}/providers/Microsoft.Authorization/roleAssignmentScheduleRequests/{guid}`

**Parameters**:
- `api-version=2020-10-01`

**Request Body**:
```json
{
  "properties": {
    "principalId": "{user-object-id}",
    "roleDefinitionId": "{scope}/providers/Microsoft.Authorization/roleDefinitions/{role-id}",
    "requestType": "SelfActivate",
    "justification": "Requested via az-pim-cli",
    "scheduleInfo": {
      "startDateTime": "{iso-timestamp}",
      "expiration": {
        "type": "AfterDuration",
        "duration": "PT8H"
      }
    },
    "ticketInfo": {
      "ticketNumber": "{ticket}",
      "ticketSystem": "{system}"
    }
  }
}
```

**Scope**: `https://management.azure.com/.default`

**Permissions Required**: 
- `Microsoft.Authorization/roleAssignmentScheduleRequests/write` at the specified scope
- Must have eligible assignment for the role

**Notes**: 
- GUID is generated client-side (UUID v4)
- Uses ARM, NOT Graph API

**Reference**: https://learn.microsoft.com/en-us/rest/api/authorization/role-assignment-schedule-requests/create

---

### List Resource Role Assignment Requests

**Command**: `az-pim history --resource --scope <scope>`

**Endpoint**: `GET https://management.azure.com/{scope}/providers/Microsoft.Authorization/roleAssignmentScheduleRequests`

**Parameters**:
- `api-version=2020-10-01`
- `$filter=asTarget()` or `principalId eq '{principal-id}'`

**Scope**: `https://management.azure.com/.default`

**Permissions Required**: 
- `Microsoft.Authorization/roleAssignmentScheduleRequests/read`

**Reference**: https://learn.microsoft.com/en-us/rest/api/authorization/role-assignment-schedule-requests/list-for-scope

---

## Subscription and Scope Resolution

### List Subscriptions

**Command**: Used internally for scope resolution

**Endpoint**: `GET https://management.azure.com/subscriptions`

**Parameters**:
- `api-version=2022-12-01`

**Scope**: `https://management.azure.com/.default`

**Permissions Required**: Standard Azure subscription access

**Reference**: https://learn.microsoft.com/en-us/rest/api/subscription/subscriptions/list

---

### List Resource Groups

**Command**: Used internally for scope resolution

**Endpoint**: `GET https://management.azure.com/subscriptions/{subscription-id}/resourceGroups`

**Parameters**:
- `api-version=2021-04-01`

**Scope**: `https://management.azure.com/.default`

**Reference**: https://learn.microsoft.com/en-us/rest/api/resources/resource-groups/list

---

## API Version Notes

- **Graph API**: Uses `/beta` for most PIM endpoints (some have v1.0, but PIM operations require beta)
- **ARM API**: Uses `2020-10-01` API version for role assignment schedule operations
- **Subscription API**: Uses `2022-12-01` API version

## Backend Selection Logic

The CLI determines which backend to use based on:

1. **Command flags**: `--resource` flag indicates ARM backend
2. **Role ID format**: 
   - Entra roles: Short GUID format (e.g., `62e90394-69f5-4237-9190-012177145e10`)
   - Resource roles: Full ARM path (e.g., `/subscriptions/.../providers/Microsoft.Authorization/roleDefinitions/...`)
3. **Environment variable**: `AZ_PIM_BACKEND` (ARM or GRAPH) - for override/testing

## Deprecated APIs (DO NOT USE)

The following APIs are deprecated and should NOT be used:

- ❌ `GET /beta/privilegedAccess/azureResources/...` - Deprecated, stops working Oct 28, 2026
- ❌ `POST /beta/privilegedAccess/azureResources/roleAssignmentRequests` - Use ARM instead

**Replacement**: Use ARM API endpoints (`Microsoft.Authorization/roleAssignmentScheduleRequests`) for Azure resource roles.

**Reference**: 
- https://docs.azure.cn/en-us/entra/id-governance/privileged-identity-management/pim-apis
- https://learn.microsoft.com/en-us/graph/api/resources/privilegedaccess?view=graph-rest-beta

## Error Handling

### Common HTTP Status Codes

- **401 Unauthorized**: Token expired or invalid - suggest `az login`
- **403 Forbidden**: Insufficient permissions - check PERMISSIONS.md
- **404 Not Found**: Resource or role not found
- **429 Too Many Requests**: Rate limiting - implement exponential backoff

### Permission Errors

When a 403 error occurs, the error message should include:
- The endpoint that failed
- The user's principal ID
- Required permissions (from PERMISSIONS.md)
- Suggested actions

## Future Enhancements

Commands planned for future iterations:

- `az-pim entra eligible` - List eligible Entra roles (explicit command, currently via `az-pim list`)
- `az-pim entra active` - List active Entra assignments
- `az-pim azure activate --scope <sub|rg|resource> --role <role>` - Explicit Azure resource activation (currently via `az-pim activate --resource`)
- `az-pim entra approvals list` - List pending approvals (explicit command, currently via `az-pim pending`)
- `az-pim entra approvals approve <request-id>` - Approve request (currently via `az-pim approve`)
- `az-pim entra approvals deny <request-id>` - Deny request
