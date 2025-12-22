# Required Permissions and Roles

This document outlines the required permissions for each command in the az-pim-cli. Understanding these permissions is critical for troubleshooting access issues and ensuring proper configuration.

## Overview

The CLI interacts with two separate permission models:

1. **Microsoft Graph Permissions** - For Entra ID (Azure AD) roles
2. **Azure RBAC Permissions** - For Azure resource roles

These are **independent** permission systems with different scopes and models.

## Authentication Prerequisites

Before using any commands, ensure you are authenticated:

```bash
# Login with Azure CLI (recommended)
az login

# Verify your account
az account show
```

See [docs/adr/0001-auth.md](adr/0001-auth.md) for detailed authentication strategy.

---

## Entra ID (Azure AD) Role Commands

These commands use **Microsoft Graph API** and require **Graph API permissions**.

### Command: `az-pim list` (Entra roles, default)

**Description**: List eligible Entra ID roles for the current user

**API Endpoint**: `GET https://graph.microsoft.com/beta/roleManagement/directory/roleEligibilityScheduleInstances`

**Required Permissions** (Delegated):
- `RoleEligibilitySchedule.Read.Directory`
- OR `RoleManagement.Read.Directory` (broader access)

**Minimum Requirements**:
- User must have at least one eligible Entra ID role assignment
- No special admin roles required for reading your own eligibilities

**Common Errors**:
```
403 Forbidden: Insufficient privileges to complete the operation
```

**Resolution**:
- Ensure you are logged in: `az login`
- Your account needs the Graph permission listed above
- Contact your tenant administrator if permission is missing

---

### Command: `az-pim activate <role>` (Entra roles)

**Description**: Activate an eligible Entra ID role

**API Endpoint**: `POST https://graph.microsoft.com/beta/roleManagement/directory/roleAssignmentScheduleRequests`

**Required Permissions** (Delegated):
- `RoleAssignmentSchedule.ReadWrite.Directory`
- OR `RoleManagement.ReadWrite.Directory` (broader access)

**Minimum Requirements**:
- User must have an **eligible** assignment for the role being activated
- Role must be configured for self-activation (no approval required, or you are the approver)

**Additional Considerations**:
- Some roles may require MFA before activation
- Some roles may require approval from designated approvers
- Role settings may enforce maximum activation duration

**Common Errors**:
```
403 Forbidden: Insufficient privileges to complete the operation
401 Unauthorized: Authentication failed
```

**Resolution**:
- Ensure you have the required Graph permission
- Verify you have an eligible assignment: `az-pim list`
- Complete MFA if prompted
- Check role settings in Azure Portal → Entra ID → PIM

---

### Command: `az-pim history` (Entra roles)

**Description**: View activation history for Entra ID roles

**API Endpoint**: `GET https://graph.microsoft.com/beta/roleManagement/directory/roleAssignmentScheduleRequests`

**Required Permissions** (Delegated):
- `RoleAssignmentSchedule.Read.Directory`
- OR `RoleManagement.Read.Directory`

**Minimum Requirements**:
- Standard user access (can see own activation history)

---

### Command: `az-pim pending` (Entra roles)

**Description**: List pending approval requests for Entra ID roles

**API Endpoint**: `GET https://graph.microsoft.com/beta/roleManagement/directory/roleAssignmentScheduleRequests/filterByCurrentUser(on='approver')`

**Required Permissions** (Delegated):
- `RoleAssignmentSchedule.Read.Directory`
- OR `RoleManagement.Read.Directory`

**Minimum Requirements**:
- User must be configured as an **approver** for one or more Entra ID roles
- Approver roles are configured in Azure Portal → Entra ID → PIM → Role Settings

**Common Errors**:
```
Empty list - No pending approvals
```

**Resolution**:
- Verify you are configured as an approver for roles
- Check that there are pending requests requiring approval

---

### Command: `az-pim approve <request-id>` (Entra roles)

**Description**: Approve a pending Entra ID role activation request

**API Endpoint**: `POST https://graph.microsoft.com/beta/roleManagement/directory/roleAssignmentScheduleRequests/{request-id}/approve`

**Required Permissions** (Delegated):
- `RoleManagement.ReadWrite.Directory`

**Minimum Requirements**:
- User must be configured as an **approver** for the specific role
- Request must be in "PendingApproval" status
- Approval must be within the approval window (typically 24 hours)

**Common Errors**:
```
403 Forbidden: User is not an approver for this role
404 Not Found: Request does not exist or has already been processed
```

**Resolution**:
- Verify you are listed as an approver in role settings
- Check that request ID is correct
- Ensure request hasn't expired or been processed

---

## Azure Resource Role Commands

These commands use **Azure Resource Manager (ARM) API** and require **Azure RBAC permissions**. They do **NOT** require Graph API permissions.

### Command: `az-pim list --resource` (Resource roles)

**Description**: List eligible Azure resource roles (subscription, resource group, resource)

**API Endpoint**: `GET https://management.azure.com/{scope}/providers/Microsoft.Authorization/roleEligibilityScheduleInstances`

**Required Permissions** (Azure RBAC):
- `Microsoft.Authorization/roleEligibilityScheduleInstances/read` at the target scope

**Minimum Requirements**:
- Reader access at the scope (subscription, resource group, or resource)
- At least one eligible role assignment at the target scope

**Scope Examples**:
- Subscription: `/subscriptions/{subscription-id}`
- Resource Group: `/subscriptions/{subscription-id}/resourceGroups/{rg-name}`
- Resource: `/subscriptions/{sub-id}/resourceGroups/{rg}/providers/{resource-type}/{resource-name}`

**Common Errors**:
```
403 Forbidden: The client does not have authorization to perform action
404 Not Found: Subscription or resource not found
```

**Resolution**:
- Verify you have access to the subscription: `az account show`
- Use `az account list` to see available subscriptions
- Check resource group exists: `az group show -n {rg-name}`
- Ensure you have eligible assignments at the target scope

---

### Command: `az-pim activate <role> --resource --scope <scope>` (Resource roles)

**Description**: Activate an eligible Azure resource role

**API Endpoint**: `PUT https://management.azure.com/{scope}/providers/Microsoft.Authorization/roleAssignmentScheduleRequests/{guid}`

**Required Permissions** (Azure RBAC):
- `Microsoft.Authorization/roleAssignmentScheduleRequests/write` at the target scope
- User must have an **eligible** assignment for the role at the scope

**Minimum Requirements**:
- Eligible role assignment at the specified scope
- Contributor or Owner eligible assignment typically grants this permission

**Common Errors**:
```
403 Forbidden: Authorization failed for resource
```

**Resolution**:
- Verify eligible assignment exists: `az-pim list --resource --scope {scope}`
- Ensure scope is correctly formatted
- Check that role activation doesn't require approval (or you are the approver)

---

### Command: `az-pim history --resource --scope <scope>` (Resource roles)

**Description**: View activation history for Azure resource roles at a scope

**API Endpoint**: `GET https://management.azure.com/{scope}/providers/Microsoft.Authorization/roleAssignmentScheduleRequests`

**Required Permissions** (Azure RBAC):
- `Microsoft.Authorization/roleAssignmentScheduleRequests/read` at the target scope

**Minimum Requirements**:
- Reader access at the scope

---

## Permission Errors and Troubleshooting

### Error: "No Azure credentials available"

**Cause**: Not logged in or credentials expired

**Resolution**:
```bash
az login
az account show
```

---

### Error: "403 Forbidden" (Graph API)

**Cause**: Missing Microsoft Graph permissions

**Resolution**:
1. Contact your Azure AD administrator
2. Request the required Graph API permissions (see command-specific sections above)
3. Administrator must grant consent in Azure Portal → App Registrations → API Permissions

**Note**: For user-delegated scenarios, permissions are often granted automatically during first use

---

### Error: "403 Forbidden" (ARM API)

**Cause**: Missing Azure RBAC permissions or no eligible role assignment

**Resolution**:
1. Verify you have access to the resource:
   ```bash
   az account show
   az group list
   ```
2. Check eligible assignments:
   ```bash
   az-pim list --resource --scope {scope}
   ```
3. Contact your subscription/resource owner to grant eligible role assignment

---

### Error: "Token expired"

**Cause**: Azure CLI token has expired

**Resolution**:
```bash
# Refresh login
az login

# Or force re-authentication
az logout
az login
```

---

## Admin Configuration Tasks

### Granting Entra ID Role Eligibility

**Portal Path**: Azure Portal → Entra ID → Privileged Identity Management → Azure AD roles → Roles → [Select Role] → Assignments → Add assignments

**Requirements**:
- Must have **Privileged Role Administrator** role
- Or **Global Administrator** role

---

### Granting Resource Role Eligibility

**Portal Path**: Azure Portal → Subscriptions → [Select Subscription] → Access Control (IAM) → Privileged access (Preview) → Add role assignment

**Requirements**:
- Must have **Owner** role at the target scope
- Or **User Access Administrator** role

---

### Configuring Role Settings

**Portal Path**: Azure Portal → Entra ID → Privileged Identity Management → [Azure AD roles or Azure resources] → Settings

**Options**:
- Require MFA for activation
- Require approval for activation
- Set maximum activation duration
- Require justification
- Configure approvers

**Requirements**:
- Must have **Privileged Role Administrator** (for Entra roles)
- Must have **Owner** or **User Access Administrator** (for resource roles)

---

## Service Principal and Automation

### Using Service Principal

For automation scenarios, configure service principal authentication:

```bash
export AZURE_CLIENT_ID="<app-id>"
export AZURE_CLIENT_SECRET="<password>"
export AZURE_TENANT_ID="<tenant-id>"
```

**Required Application Permissions** (for Entra roles):
- `RoleManagement.ReadWrite.Directory` (Application permission)

**Required Azure RBAC** (for resource roles):
- Eligible role assignments for the service principal at target scopes

---

### Using Managed Identity

For Azure VM or Azure services:

**Setup**:
1. Enable managed identity on the resource
2. Grant eligible role assignments to the managed identity
3. CLI will automatically use managed identity when run on the resource

**No configuration needed** - `DefaultAzureCredential` handles this automatically

---

## Permission Summary Table

| Command | API | Delegated Permission | Application Permission | Azure RBAC |
|---------|-----|---------------------|----------------------|------------|
| `az-pim list` (Entra) | Graph | `RoleEligibilitySchedule.Read.Directory` | `RoleManagement.Read.All` | N/A |
| `az-pim activate` (Entra) | Graph | `RoleAssignmentSchedule.ReadWrite.Directory` | `RoleManagement.ReadWrite.Directory` | N/A |
| `az-pim history` (Entra) | Graph | `RoleAssignmentSchedule.Read.Directory` | `RoleManagement.Read.All` | N/A |
| `az-pim pending` (Entra) | Graph | `RoleAssignmentSchedule.Read.Directory` | `RoleManagement.Read.All` | N/A |
| `az-pim approve` (Entra) | Graph | `RoleManagement.ReadWrite.Directory` | `RoleManagement.ReadWrite.Directory` | N/A |
| `az-pim list --resource` | ARM | N/A | N/A | `*/read` at scope |
| `az-pim activate --resource` | ARM | N/A | N/A | `Microsoft.Authorization/roleAssignmentScheduleRequests/write` |
| `az-pim history --resource` | ARM | N/A | N/A | `Microsoft.Authorization/roleAssignmentScheduleRequests/read` |

---

## References

### Microsoft Graph Permissions
- https://learn.microsoft.com/en-us/graph/permissions-reference
- https://learn.microsoft.com/en-us/graph/api/resources/privilegedidentitymanagementv3-overview

### Azure RBAC Permissions
- https://learn.microsoft.com/en-us/azure/role-based-access-control/permissions-reference
- https://learn.microsoft.com/en-us/rest/api/authorization/

### PIM Documentation
- https://learn.microsoft.com/en-us/entra/id-governance/privileged-identity-management/pim-configure
- https://learn.microsoft.com/en-us/entra/id-governance/privileged-identity-management/pim-approval-workflow

### Authentication
- See [docs/adr/0001-auth.md](adr/0001-auth.md) for authentication strategy

---

## Getting Help

If you encounter permission errors:

1. **Check this document** for the specific command requirements
2. **Verify authentication**: `az account show`
3. **Check eligible roles**: `az-pim list` (for Entra) or `az-pim list --resource` (for Azure)
4. **Enable verbose mode**: `az-pim list --verbose` to see detailed error messages
5. **Contact administrator**: Share the specific permission name from this document

For security reasons, the CLI cannot grant permissions. Contact your Azure administrator or tenant administrator to request required access.
