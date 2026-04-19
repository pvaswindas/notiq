# Admin Update Rate Limit Config API

## 1. Endpoint and Method
- Method: `PUT`
- Path: `/admin/rate-limit-configs/{config_id}`
- Handler: `AdminControllerFactory.update_rate_limit_config`

## 2. Headers
- `Content-Type: application/json` (required)
- `Authorization: Bearer <admin_jwt>` (required)

## 3. Request Payload
- Path parameter:
  - `config_id` (`string`, required): Existing rate-limit configuration identifier.
- Body fields:
  - `workspace_id` (`string | null`, optional)
  - `scope` (`string`, required)
  - `key` (`string`, required)
  - `limit` (`integer`, required)
  - `window_seconds` (`integer`, required)

### Authorization Requirement
- Caller must have the `manage_rate_limits` permission.

### Example Request JSON
```json
{
  "workspace_id": "ws_abc123",
  "scope": "channel",
  "key": "ch_5a5f6e7e7d4f4eb4b8d4a5d7",
  "limit": 10,
  "window_seconds": 60
}
```

## 4. Response
### Success (`200 OK`)
```json
{
  "id": "rlc_1234567890abcdef12345678",
  "workspace_id": "ws_abc123",
  "scope": "channel",
  "key": "ch_5a5f6e7e7d4f4eb4b8d4a5d7",
  "limit": 10,
  "window_seconds": 60
}
```

### Error Responses
- `400 Bad Request`: Invalid scope or blank key.
- `401 Unauthorized`: Missing or invalid admin token.
- `403 Forbidden`: Authenticated admin lacks `manage_rate_limits`.
- `404 Not Found`: Rate-limit config does not exist for the supplied id and workspace scope.
- `422 Unprocessable Entity`: Invalid request shape.

## 5. Internal Processing Flow After Request
1. Decode and authorize the admin JWT.
2. Load the current config for the supplied `config_id` and workspace scope.
3. Normalize scope and key.
4. Persist the updated `RateLimitConfig`.
5. Write an audit log with before and after state.

## 6. What To Do Next
- Re-check the effective throttling behavior if you changed scope or key because worker lookups are scope-sensitive.
- Keep documentation and operational runbooks aligned with the final scope definitions.
