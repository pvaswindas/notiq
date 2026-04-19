# Admin Get Resource Audit Logs API

## 1. Endpoint and Method
- Method: `GET`
- Path: `/admin/audit-logs/{resource}/{resource_id}`
- Handler: `AdminAuditControllerFactory.get_resource_audit_logs`

## 2. Headers
- `Authorization: Bearer <admin_jwt>` (required)

## 3. Request Payload
- Path parameters:
  - `resource` (`string`, required): Resource type, such as `role`, `admin`, `api_key`, or `rate_limit_config`.
  - `resource_id` (`string`, required): Resource identifier.
- Optional query parameters:
  - `page` (`integer`, default `1`, minimum `1`)
  - `page_size` (`integer`, default `50`, minimum `1`, maximum `200`)

### Authorization Requirement
- Caller must have the `view_audit_logs` permission.

## 4. Response
### Success (`200 OK`)
```json
{
  "page": 1,
  "page_size": 50,
  "has_more": false,
  "items": [
    {
      "id": "audit_002",
      "actor_id": "admin_123",
      "action": "role.assign_permission",
      "resource": "role",
      "resource_id": "role_ops",
      "before": {
        "permissions": ["view_audit_logs"]
      },
      "after": {
        "permissions": ["view_audit_logs", "manage_rate_limits"]
      },
      "metadata": {
        "permission_id": "perm_manage_rate_limits",
        "permission_name": "manage_rate_limits"
      },
      "created_at": "2026-04-16T10:50:00+00:00"
    }
  ]
}
```

### Error Responses
- `401 Unauthorized`: Missing or invalid admin token.
- `403 Forbidden`: Authenticated admin lacks `view_audit_logs`.
- `422 Unprocessable Entity`: Invalid pagination parameters.

## 5. Internal Processing Flow After Request
1. Decode and authorize the admin JWT.
2. Query audit logs by exact `resource` and `resource_id`.
3. Fetch one extra row to compute `has_more`.
4. Return paginated results in the same shape as the generic audit listing endpoint.

## 6. What To Do Next
- Use this endpoint for incident review or change-history reconstruction of one object.
- If no entries appear, widen the search to `/admin/audit-logs` in case the resource type was misidentified.
