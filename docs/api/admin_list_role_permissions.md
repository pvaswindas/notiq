# List Role Permissions API

## 1. Endpoint and Method
- Method: `GET`
- Path: `/admin/roles/{role_id}/permissions`
- Handler: `AdminControllerFactory.list_role_permissions`

## 2. Headers
- `Content-Type: application/json` (recommended)
- `Authorization: Bearer <admin_jwt>` (required)

## 3. Request Payload
- None.
- Path parameter:
  - `role_id` (`string`, required): Role id whose permissions are requested.

### Example Request
```http
GET /admin/roles/role_01/permissions HTTP/1.1
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
- `404 Not Found`: Role does not exist.

## 5. Internal Processing Flow After Request
1. Authenticate caller JWT.
2. Validate role exists.
3. Load role-permission mappings.
4. Return permission DTO list.

## 6. What To Do Next
- Compare role permission set against intended least-privilege design.
- Add/remove permissions through role assignment endpoints.
