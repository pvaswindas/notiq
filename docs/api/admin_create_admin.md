# Create Admin API

## 1. Endpoint and Method
- Method: `POST`
- Path: `/admin/admins`
- Handler: `AdminControllerFactory.create_admin`

## 2. Headers
- `Content-Type: application/json` (required)
- `Authorization: Bearer <admin_jwt>` (required)

## 3. Request Payload

### Body Schema
- `name` (`string`, required, min 1, max 255): Admin display name.
- `email` (`string`, required, min 3, max 255): Admin email (normalized to lowercase).
- `password` (`string`, required, min 8, max 256): Password used to generate bcrypt hash.
- `role_ids` (`array<string>`, optional, default `[]`): Initial role ids.

### Example Request JSON
```json
{
  "name": "Operations Admin",
  "email": "ops@example.com",
  "password": "StrongPassword123",
  "role_ids": ["role_manage_admins"]
}
```

## 4. Response
### Success (`201 Created`)
```json
{
  "id": "adm_02",
  "name": "Operations Admin",
  "email": "ops@example.com",
  "is_active": true,
  "created_at": "2026-04-01T19:22:10+00:00",
  "roles": ["manage-admins"]
}
```

### Error Responses
- `401 Unauthorized`: Missing/invalid admin bearer token.
- `403 Forbidden`: Caller lacks `manage_admins` permission.
- `400 Bad Request`: Invalid required field after normalization.
- `404 Not Found`: One of `role_ids` does not exist.
- `409 Conflict`: Admin email already exists.
- `422 Unprocessable Entity`: Invalid request schema.

## 5. Internal Processing Flow After Request
1. Authenticate caller and enforce `manage_admins` permission.
2. Validate and normalize input.
3. Check duplicate email.
4. Verify each requested role exists.
5. Hash password.
6. Persist admin record.
7. Persist admin-role links.
8. Reload role names and return response DTO.

## 6. What To Do Next
- Verify operator can log in via `/admin/auth/login`.
- Add/remove roles later using `/admin/admins/{admin_id}/roles`.
