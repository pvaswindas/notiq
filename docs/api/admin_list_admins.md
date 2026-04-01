# List Admins API

## 1. Endpoint and Method
- Method: `GET`
- Path: `/admin/admins`
- Handler: `AdminControllerFactory.list_admins`

## 2. Headers
- `Content-Type: application/json` (recommended)
- `Authorization: Bearer <admin_jwt>` (required)

## 3. Request Payload
- None.

### Example Request
```http
GET /admin/admins HTTP/1.1
Host: localhost:8000
Authorization: Bearer <jwt>
```

## 4. Response
### Success (`200 OK`)
```json
[
  {
    "id": "adm_01",
    "name": "Platform Admin",
    "email": "admin@example.com",
    "is_active": true,
    "created_at": "2026-03-31T15:00:00+00:00",
    "roles": ["platform-admin"]
  }
]
```

### Error Responses
- `401 Unauthorized`: Missing/invalid admin bearer token.
- `403 Forbidden`: Caller lacks `manage_admins` permission.

## 5. Internal Processing Flow After Request
1. Authenticate caller and enforce `manage_admins` permission.
2. Load all admin records.
3. For each admin, resolve assigned roles.
4. Return enriched admin list.

## 6. What To Do Next
- Use response ids for role assignment and disable operations.
- Audit inactive/over-privileged admins regularly.
