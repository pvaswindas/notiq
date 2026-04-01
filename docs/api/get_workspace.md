# Get Workspace API

## 1. Endpoint and Method
- Method: `GET`
- Path: `/workspaces/{workspace_id}`
- Handler: `WorkspaceControllerFactory.get_workspace`

## 2. Headers
- `Content-Type: application/json` (recommended)
- `Authorization`: not required by current route implementation.

## 3. Request Payload
- None.
- Path parameter:
  - `workspace_id` (`string`, required): Workspace identifier.

### Example Request
```http
GET /workspaces/ws_f47ac10b58cc4372a5670e02 HTTP/1.1
Host: localhost:8000
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
{
  "id": "ws_f47ac10b58cc4372a5670e02",
  "name": "Acme Payments"
}
```

### Error Responses
- `400 Bad Request`: Blank workspace ID.
- `404 Not Found`: Workspace does not exist.

## 5. Internal Processing Flow After Request
1. Validate and normalize path parameter.
2. Query workspace repository by ID.
3. Return 404 when absent.
4. Map domain object to API response.

## 6. What To Do Next
- Use returned workspace ID to create/list channels and API keys.
