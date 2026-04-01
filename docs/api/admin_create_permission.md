# Create Permission API

## 1. Endpoint and Method
- Method: `POST`
- Path: `/admin/permissions`
- Handler: `AdminControllerFactory.create_permission`

## 2. Headers
- `Content-Type: application/json` (required)
- `Authorization: Bearer <admin_jwt>` (required)

## 3. Request Payload

### Body Schema
- `name` (`string`, required, min 1, max 128): Permission name, trimmed before persistence.

### Example Request JSON
```json
{
  "name": "manage_integrations"
}
```

## 4. Response
### Success (`201 Created`)
```json
{
  "id": "perm_01",
  "name": "manage_integrations",
  "created_at": "2026-04-01T19:40:00+00:00"
}
```

### Error Responses
- `401 Unauthorized`: Missing/invalid admin bearer token.
- `403 Forbidden`: Caller lacks `manage_permissions` permission.
- `400 Bad Request`: Name is blank after trim.
- `409 Conflict`: Permission already exists.
- `422 Unprocessable Entity`: Invalid request schema.

## 5. Internal Processing Flow After Request
1. Authenticate caller and enforce `manage_permissions` permission.
2. Trim and validate permission name.
3. Check for existing permission by name.
4. Persist permission.
5. Return created permission DTO.

## 6. What To Do Next
- Attach permission to a role using `/admin/roles/{role_id}/permissions`.
- Keep permission names action-oriented and stable.
