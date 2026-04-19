# List Provider Accounts API

## 1. Endpoint and Method
- Method: `GET`
- Path: `/provider-accounts`
- Handler: `ProviderAccountControllerFactory.list_provider_accounts`

## 2. Headers
- `Content-Type: application/json` (recommended)
- `Authorization: Bearer <api_key>` (required)

## 3. Request Payload
- Query parameter:
  - `workspace_id` (`string`, required): Workspace identifier. Must match the authenticated API key workspace.

### Example Request
```http
GET /provider-accounts?workspace_id=ws_abc123 HTTP/1.1
Host: localhost:8000
Authorization: Bearer notiq_xxx
```

## 4. Response
### Success (`200 OK`)
```json
[
  {
    "id": "pa_telegram_ops",
    "workspace_id": "ws_abc123",
    "provider": "telegram",
    "is_active": true,
    "created_at": "2026-04-16T10:10:00+00:00"
  }
]
```

### Error Responses
- `400 Bad Request`: Blank workspace id.
- `403 Forbidden`: Authenticated API key does not belong to `workspace_id`.
- `404 Not Found`: Workspace does not exist.

## 5. Internal Processing Flow After Request
1. Validate query parameter and authenticated API key.
2. Enforce workspace ownership.
3. `ListProviderAccountsUseCase` validates the workspace exists.
4. Repository loads provider accounts for that workspace.
5. Route returns a transport-safe list that deliberately omits credentials.

## 6. What To Do Next
- Use the list to choose which provider account should back a new managed channel.
- Use `GET /provider-accounts/{provider_account_id}` when validating a specific account reference.
