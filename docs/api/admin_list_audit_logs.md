# Admin List Audit Logs API

## 1. Endpoint and Method
- Method: `GET`
- Path: `/admin/audit-logs`
- Handler: `AdminAuditControllerFactory.list_audit_logs`

## 2. Headers
- `Authorization: Bearer <admin_jwt>` (required)
- `Content-Type: application/json` is optional.

## 3. Request Payload
- Optional query parameters:
  - `actor_id` (`string`)
  - `resource` (`string`)
  - `action` (`string`)
  - `from_date` (`datetime`)
  - `to_date` (`datetime`)
  - `page` (`integer`, default `1`, minimum `1`)
  - `page_size` (`integer`, default `50`, minimum `1`, maximum `200`)

### Authorization Requirement
- Caller must have the `view_audit_logs` permission.

### Example Request
```http
GET /admin/audit-logs?resource=rate_limit_config&action=rate_limit.update&page=1&page_size=20 HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJ...
```

## 4. Response
### Success (`200 OK`)
```json
{
  "page": 1,
  "page_size": 20,
  "has_more": false,
  "items": [
    {
      "id": "audit_001",
      "actor_id": "admin_123",
      "action": "rate_limit.update",
      "resource": "rate_limit_config",
      "resource_id": "rlc_1234567890abcdef12345678",
      "before": {
        "limit": 30
      },
      "after": {
        "limit": 10
      },
      "metadata": null,
      "created_at": "2026-04-16T10:45:00+00:00"
    }
  ]
}
```

### Error Responses
- `401 Unauthorized`: Missing or invalid admin token.
- `403 Forbidden`: Authenticated admin lacks `view_audit_logs`.
- `422 Unprocessable Entity`: Invalid pagination or datetime filters.

## 5. Internal Processing Flow After Request
1. Decode and authorize the admin JWT.
2. Translate page and page size into repository offset and fetch limit.
3. Query the audit log repository with the supplied filters.
4. Fetch one extra row to determine `has_more`.
5. Return paginated audit records in a stable HTTP DTO.

## 6. What To Do Next
- Use resource-specific lookup when investigating a single object history.
- Narrow filters aggressively in production because audit volume can grow quickly.
