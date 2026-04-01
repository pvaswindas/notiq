# Create API Key API

## 1. Endpoint and Method
- Method: `POST`
- Path: `/workspaces/{workspace_id}/api-keys`
- Handler: `ApiKeyControllerFactory.create_api_key`

## 2. Headers
- `Content-Type: application/json` (required)
- `Authorization: Bearer <api_key>` (required)

## 3. Request Payload

### Path Parameter
- `workspace_id` (`string`, required): Target workspace for key creation.

### Body Schema
- `name` (`string`, required, min 1, max 128): Label for operational key management.

### Example Request JSON
```json
{
  "name": "ci-ingestion-key"
}
```

## 4. Response
### Success (`201 Created`)
```json
{
  "api_key": "notiq_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "name": "ci-ingestion-key"
}
```

### Error Responses
- `401 Unauthorized`: Missing/malformed authorization header.
- `403 Forbidden`: Authenticated key belongs to a different workspace or key is invalid/disabled.
- `404 Not Found`: Workspace not found.
- `400 Bad Request`: Name is blank after trimming.
- `422 Unprocessable Entity`: Request schema invalid.

## 5. Internal Processing Flow After Request
1. Authenticate request via Bearer API key.
2. Enforce workspace ownership (`auth.workspace_id == path workspace_id`).
3. Verify workspace exists.
4. Generate raw API key.
5. Hash raw key and persist hash only.
6. Return raw API key one time in response.

## 6. What To Do Next
- Store the raw key securely; it is not recoverable later.
- Use the returned key for `/events` and API-key management requests.
