# List API Keys API

## 1. Endpoint and Method
- Method: `GET`
- Path: `/workspaces/{workspace_id}/api-keys`
- Handler: `ApiKeyControllerFactory.list_api_keys`

## 2. Headers
- `Content-Type: application/json` (recommended)
- `Authorization: Bearer <api_key>` (required)

## 3. Request Payload
- None.
- Path parameter:
  - `workspace_id` (`string`, required): Workspace whose keys are listed.

### Example Request
```http
GET /workspaces/ws_f47ac10b58cc4372a5670e02/api-keys HTTP/1.1
Host: localhost:8000
Authorization: Bearer notiq_xxx
```

### Example Request JSON (Path Parameters)
```json
{
  "workspace_id": "ws_f47ac10b58cc4372a5670e02"
}
```

## 4. Response
### Success (`200 OK`)
```json
[
  {
    "id": "key_43a0fae6730f4f6d9235f2ea",
    "workspace_id": "ws_f47ac10b58cc4372a5670e02",
    "name": "ci-ingestion-key",
    "masked_key": "notiq_****",
    "is_active": true,
    "created_at": "2026-03-31T16:22:41.138262+00:00"
  }
]
```

### Error Responses
- `401 Unauthorized`: Missing/malformed authorization header.
- `403 Forbidden`: Invalid/disabled key or workspace access denied.
- `404 Not Found`: Workspace not found.

## 5. Internal Processing Flow After Request
1. Authenticate API key.
2. Enforce workspace ownership.
3. Verify workspace exists.
4. Load API keys sorted by newest first.
5. Return masked-only key representations.

## 6. What To Do Next
- Disable obsolete keys using the disable endpoint.
- Rotate keys by creating a new key before disabling old keys.
