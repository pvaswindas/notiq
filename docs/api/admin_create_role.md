# Create Role API

## 1. Endpoint and Method
- Method: `POST`
- Path: `/admin/roles`
- Handler: `AdminControllerFactory.create_role`

## 2. Headers
- `Content-Type: application/json` (required)
- `Authorization: Bearer <admin_jwt>` (required)

## 3. Request Payload

### Body Schema
- `name` (`string`, required, min 1, max 128): Role name, trimmed before persistence.

### Example Request JSON
```json
{
  "name": "incident-operator"
}
```

## 4. Response
### Success (`201 Created`)
```json
{
  "id": "role_01",
  "name": "incident-operator",
  "created_at": "2026-04-01T19:35:00+00:00"
}
```

### Error Responses
- `401 Unauthorized`: Missing/invalid admin bearer token.
- `403 Forbidden`: Caller lacks `manage_roles` permission.
- `400 Bad Request`: Name is blank after trim.
- `409 Conflict`: Role already exists.
- `422 Unprocessable Entity`: Invalid request schema.

## 5. Internal Processing Flow After Request
1. Authenticate caller and enforce `manage_roles` permission.
2. Trim and validate role name.
3. Check for existing role by name.
4. Persist new role.
5. Return created role DTO.

## 6. What To Do Next
- Assign permissions using `/admin/roles/{role_id}/permissions`.
- Assign role to admins using `/admin/admins/{admin_id}/roles`.
