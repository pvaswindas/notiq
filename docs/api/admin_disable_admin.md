# Disable Admin API

## 1. Endpoint and Method
- Method: `PATCH`
- Path: `/admin/admins/{admin_id}/disable`
- Handler: `AdminControllerFactory.disable_admin`

## 2. Headers
- `Content-Type: application/json` (recommended)
- `Authorization: Bearer <admin_jwt>` (required)

## 3. Request Payload
- None.
- Path parameter:
  - `admin_id` (`string`, required): Target admin id.

### Example Request
```http
PATCH /admin/admins/adm_02/disable HTTP/1.1
Host: localhost:8000
Authorization: Bearer <jwt>
```

## 4. Response
### Success (`200 OK`)
```json
{
  "id": "adm_02",
  "name": "Operations Admin",
  "email": "ops@example.com",
  "is_active": false,
  "created_at": "2026-04-01T19:22:10+00:00",
  "roles": ["manage-admins"]
}
```

### Error Responses
- `401 Unauthorized`: Missing/invalid admin bearer token.
- `403 Forbidden`: Caller lacks `manage_admins` permission.
- `404 Not Found`: Admin not found.

## 5. Internal Processing Flow After Request
1. Authenticate caller and enforce `manage_admins` permission.
2. Set `is_active=false` for the target admin.
3. If missing, return `404`.
4. Load assigned roles.
5. Return updated admin projection.

## 6. What To Do Next
- Ensure disabled admins are removed from operational runbooks.
- Keep at least one active privileged admin available for recovery.
