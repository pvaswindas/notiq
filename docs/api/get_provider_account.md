# Get Provider Account API

## 1. Endpoint and Method
- Method: `GET`
- Path: `/provider-accounts/{provider_account_id}`
- Handler: `ProviderAccountControllerFactory.get_provider_account`

## 2. Headers
- `Content-Type: application/json` (recommended)
- `Authorization: Bearer <api_key>` (required)

## 3. Request Payload
- Path parameter:
  - `provider_account_id` (`string`, required): Provider account identifier.

### Example Request
```http
GET /provider-accounts/pa_telegram_ops HTTP/1.1
Host: localhost:8000
Authorization: Bearer notiq_xxx
```

## 4. Response
### Success (`200 OK`)
```json
{
  "id": "pa_telegram_ops",
  "workspace_id": "ws_abc123",
  "provider": "telegram",
  "is_active": true,
  "created_at": "2026-04-16T10:10:00+00:00"
}
```

### Error Responses
- `400 Bad Request`: Invalid provider account identifier.
- `403 Forbidden`: The account does not belong to the authenticated workspace.
- `404 Not Found`: Provider account does not exist.

## 5. Internal Processing Flow After Request
1. Validate path parameter and authenticated API key.
2. `GetProviderAccountUseCase` loads the provider account by id.
3. The use case verifies that the caller's workspace is allowed to see the account.
4. Route returns a response that exposes metadata but never the credential payload.

## 6. What To Do Next
- Use the account in channel creation.
- If the account is missing or belongs to another workspace, create or request the correct workspace-scoped account instead of reusing it across tenants.
