# Assign Role To Admin API

## 1. Endpoint and Method
- Method: `POST`
- Path: `/admin/admins/{admin_id}/roles`
- Handler: `AdminControllerFactory.assign_role`

## 2. Headers
- `Content-Type: application/json` (required)
- `Authorization: Bearer <admin_jwt>` (required)

## 3. Request Payload

### Path Parameter
- `admin_id` (`string`, required): Target admin id.

### Body Schema
- `role_id` (`string`, required): Role id to assign.

### Example Request JSON
```json
{
  "role_id": "role_manage_roles"
}
```

## 4. Response
### Success (`204 No Content`)
- Empty response body.

### Error Responses
- `401 Unauthorized`: Missing/invalid admin bearer token.
- `403 Forbidden`: Caller lacks `manage_admins` permission.
- `404 Not Found`: Target admin or role does not exist.
- `422 Unprocessable Entity`: Invalid request schema.

## 5. Internal Processing Flow After Request
1. Authenticate caller and enforce `manage_admins` permission.
2. Validate path/body schema.
3. Verify target admin exists.
4. Verify requested role exists.
5. Persist admin-role assignment.
6. Return no-content success.

## 6. What To Do Next
- Confirm effective permissions via `/admin/me` (for target admin login) or `/admin/admins`.
- Keep role assignments minimal to least privilege.
