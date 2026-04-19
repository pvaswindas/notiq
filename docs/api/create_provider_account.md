# Create Provider Account API

## 1. Endpoint and Method
- Method: `POST`
- Path: `/provider-accounts`
- Handler: `ProviderAccountControllerFactory.create_provider_account`

## 2. Headers
- `Content-Type: application/json` (required)
- `Authorization: Bearer <api_key>` (required)

## 3. Request Payload
- `workspace_id` (`string`, required): Workspace that owns the provider account. Must match the authenticated API key workspace.
- `provider` (`string`, required): Provider key such as `telegram` or `email`.
- `credentials` (`object`, optional, default `{}`): Structured provider credentials validated by `ProviderConfigurationValidator`.

### Example Request JSON
```json
{
  "workspace_id": "ws_abc123",
  "provider": "telegram",
  "credentials": {
    "bot_token": "123456:telegram-bot-token"
  }
}
```

## 4. Response
### Success (`201 Created`)
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
- `400 Bad Request`: Invalid provider name or invalid credential shape.
- `403 Forbidden`: Authenticated API key does not belong to `workspace_id`.
- `404 Not Found`: Workspace does not exist.
- `422 Unprocessable Entity`: Request schema invalid.

## 5. Internal Processing Flow After Request
1. Validate request schema and authenticated API key.
2. Enforce workspace ownership.
3. `CreateProviderAccountUseCase` verifies the workspace exists.
4. `ProviderConfigurationValidator` validates the structured credential payload for the chosen provider.
5. The use case generates a provider-account ID and persists the account.
6. Audit metadata is attached so creation is traceable.
7. The route returns a response without echoing credentials.

## 6. What To Do Next
- Use the returned provider account when creating channels.
- If the provider requires rotation later, create a new provider account and move channels to it intentionally.
