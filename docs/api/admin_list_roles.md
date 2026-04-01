# List Roles API

## 1. Endpoint and Method
- Method: `GET`
- Path: `/admin/roles`
- Handler: `AdminControllerFactory.list_roles`

## 2. Headers
- `Content-Type: application/json` (recommended)
- `Authorization: Bearer <admin_jwt>` (required)

## 3. Request Payload
- None.

### Example Request
```http
GET /admin/roles HTTP/1.1
Host: localhost:8000
Authorization: Bearer <jwt>
```

## 4. Response
### Success (`200 OK`)
```json
[
  {
    "id": "role_01",
    "name": "incident-operator",
    "created_at": "2026-04-01T19:35:00+00:00"
  }
]
```

### Error Responses
- `401 Unauthorized`: Missing/invalid admin bearer token.

## 5. Internal Processing Flow After Request
1. Authenticate caller JWT.
2. Load all roles.
3. Return role DTO list.

## 6. What To Do Next
- Use role ids to assign permissions and admin memberships.
- Periodically prune unused roles.
