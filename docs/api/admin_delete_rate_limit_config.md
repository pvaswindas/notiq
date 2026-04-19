# Admin Delete Rate Limit Config API

## 1. Endpoint and Method
- Method: `DELETE`
- Path: `/admin/rate-limit-configs/{config_id}`
- Handler: `AdminControllerFactory.delete_rate_limit_config`

## 2. Headers
- `Authorization: Bearer <admin_jwt>` (required)
- `Content-Type: application/json` is not required.

## 3. Request Payload
- Path parameter:
  - `config_id` (`string`, required): Rate-limit config identifier.
- Optional query parameter:
  - `workspace_id` (`string`, optional): Used to disambiguate workspace-scoped lookup before deletion.

### Authorization Requirement
- Caller must have the `manage_rate_limits` permission.

## 4. Response
### Success (`204 No Content`)
- Empty response body.

### Error Responses
- `401 Unauthorized`: Missing or invalid admin token.
- `403 Forbidden`: Authenticated admin lacks `manage_rate_limits`.
- `404 Not Found`: Rate-limit config does not exist.

## 5. Internal Processing Flow After Request
1. Decode and authorize the admin JWT.
2. Load the current config using `config_id` and optional `workspace_id`.
3. Delete the config from the repository.
4. Write an audit log containing the deleted record in the `before` payload.

## 6. What To Do Next
- Future worker executions will stop seeing this override once repository reads no longer return it.
- Confirm whether a fallback global or environment-based limit now applies.
