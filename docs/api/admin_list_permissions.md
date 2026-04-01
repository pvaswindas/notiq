# List Permissions API

## 1. Endpoint and Method
- Method: `GET`
- Path: `/admin/permissions`
- Handler: `AdminControllerFactory.list_permissions`

## 2. Headers
- `Content-Type: application/json` (recommended)
- `Authorization: Bearer <admin_jwt>` (required)

## 3. Request Payload
- None.

### Example Request
```http
GET /admin/permissions HTTP/1.1
Host: localhost:8000
Authorization: Bearer <jwt>
```

## 4. Response
### Success (`200 OK`)
```json
[
  {
    "id": "perm_01",
    "name": "manage_integrations",
    "created_at": "2026-04-01T19:40:00+00:00"
  }
]
```

### Error Responses
- `401 Unauthorized`: Missing/invalid admin bearer token.

## 5. Internal Processing Flow After Request
1. Authenticate caller JWT.
2. Load all permissions.
3. Return permission DTO list.

## 6. What To Do Next
- Use permission ids in role binding endpoint.
- Review for redundant or overlapping permission names.
