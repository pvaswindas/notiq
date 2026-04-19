# Admin Create Rate Limit Config API

## 1. Endpoint and Method
- Method: `POST`
- Path: `/admin/rate-limit-configs`
- Handler: `AdminControllerFactory.create_rate_limit_config`

## 2. Headers
- `Content-Type: application/json` (required)
- `Authorization: Bearer <admin_jwt>` (required)

## 3. Request Payload
- `workspace_id` (`string | null`, optional): Optional tenant scope. `null` means the config is not tied to a workspace.
- `scope` (`string`, required): One of `group`, `provider`, `tenant`, `global`, or `channel`.
- `key` (`string`, required): Scope-specific lookup key.
- `limit` (`integer`, required): Allowed operations in the window.
- `window_seconds` (`integer`, required): Rolling window size in seconds.

### Authorization Requirement
- Caller must have the `manage_rate_limits` permission.

### Example Request JSON
```json
{
  "workspace_id": "ws_abc123",
  "scope": "channel",
  "key": "ch_5a5f6e7e7d4f4eb4b8d4a5d7",
  "limit": 30,
  "window_seconds": 60
}
```

## 4. Response
### Success (`201 Created`)
```json
{
  "id": "rlc_1234567890abcdef12345678",
  "workspace_id": "ws_abc123",
  "scope": "channel",
  "key": "ch_5a5f6e7e7d4f4eb4b8d4a5d7",
  "limit": 30,
  "window_seconds": 60
}
```

### Error Responses
- `400 Bad Request`: Invalid scope or blank key.
- `401 Unauthorized`: Missing or invalid admin token.
- `403 Forbidden`: Authenticated admin lacks `manage_rate_limits`.
- `422 Unprocessable Entity`: Invalid request shape.

## 5. Internal Processing Flow After Request
1. Decode and authorize the admin JWT.
2. Normalize scope and trim the key.
3. Build a `RateLimitConfig` domain entity.
4. Persist the config in the repository.
5. Write an audit log entry describing the created record.

## 6. What To Do Next
- The new config becomes available to `DeliverySafetyService` for future job execution.
- If the config targets a workspace or channel, verify the key matches the identifiers the worker will actually use.
