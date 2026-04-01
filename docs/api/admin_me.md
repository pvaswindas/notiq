# Admin Profile API

## 1. Endpoint and Method
- Method: `GET`
- Path: `/admin/me`
- Handler: `AdminControllerFactory.me`

## 2. Headers
- `Content-Type: application/json` (recommended)
- `Authorization: Bearer <admin_jwt>` (required)

## 3. Request Payload
- None.

### Example Request
```http
GET /admin/me HTTP/1.1
Host: localhost:8000
Authorization: Bearer <jwt>
```

## 4. Response
### Success (`200 OK`)
```json
{
  "id": "adm_01",
  "name": "Platform Admin",
  "email": "admin@example.com",
  "is_active": true,
  "created_at": "2026-03-31T15:00:00+00:00",
  "roles": ["platform-admin"],
  "permissions": ["manage_admins", "manage_roles", "manage_permissions"]
}
```

### Error Responses
- `401 Unauthorized`: Missing/invalid admin bearer token.
- `404 Not Found`: Admin referenced in token does not exist.

## 5. Internal Processing Flow After Request
1. Validate bearer token structure.
2. Decode JWT and extract `admin_id` and role claims.
3. Load admin by id.
4. Load current roles and effective permissions from repositories.
5. Return profile projection.

## 6. What To Do Next
- Use this endpoint to verify current operator identity and effective access.
- If permissions are missing, update role assignments instead of bypassing checks.
