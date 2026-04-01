# List Workspaces API

## 1. Endpoint and Method
- Method: `GET`
- Path: `/workspaces`
- Handler: `WorkspaceControllerFactory.list_workspaces`

## 2. Headers
- `Content-Type: application/json` (recommended)
- `Authorization`: not required by current route implementation.

## 3. Request Payload
- None.

### Example Request
```http
GET /workspaces HTTP/1.1
Host: localhost:8000
```

### Example Request JSON
```json
{}
```

## 4. Response
### Success (`200 OK`)
```json
[
  {
    "id": "ws_f47ac10b58cc4372a5670e02",
    "name": "Acme Payments"
  },
  {
    "id": "ws_7af8bd120ec045a5a53a4bc1",
    "name": "Globex"
  }
]
```

### Error Responses
- No custom error mapping in route; framework/runtime failures surface as `500`.

## 5. Internal Processing Flow After Request
1. Execute workspace listing use case.
2. Fetch all workspace records from repository.
3. Map each domain workspace to response DTO.

## 6. What To Do Next
- Select a workspace ID and proceed with channel or API-key management.
