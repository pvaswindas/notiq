# Assign Permission To Role API

## 1. Endpoint and Method
- Method: `POST`
- Path: `/admin/roles/{role_id}/permissions`
- Handler: `AdminControllerFactory.assign_permission`

## 2. Headers
- `Content-Type: application/json` (required)
- `Authorization: Bearer <admin_jwt>` (required)

## 3. Request Payload

### Path Parameter
- `role_id` (`string`, required): Role id to update.

### Body Schema
- `permission_id` (`string`, required): Permission id to assign to role.

### Example Request JSON
```json
{
  "permission_id": "perm_01"
}
```

## 4. Response
### Success (`204 No Content`)
- Empty response body.

### Error Responses
- `401 Unauthorized`: Missing/invalid admin bearer token.
- `403 Forbidden`: Caller lacks `manage_roles` permission.
- `404 Not Found`: Role or permission does not exist.
- `422 Unprocessable Entity`: Invalid request schema.

## 5. Internal Processing Flow After Request
1. Authenticate caller and enforce `manage_roles` permission.
2. Validate role exists.
3. Validate permission exists.
4. Persist role-permission assignment.
5. Return no-content success.

## 6. What To Do Next
- Validate effective access by logging in as an admin with that role and calling protected endpoints.
- Track permission grants in change-management workflows.
