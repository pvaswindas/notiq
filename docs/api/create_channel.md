# Create Channel API

## 1. Endpoint and Method
- Method: `POST`
- Path: `/channels`
- Handler: `ChannelControllerFactory.create_channel`

## 2. Headers
- `Content-Type: application/json` (required)
- `Authorization: Bearer <api_key>` (required)

## 3. Request Payload
- `workspace_id` (`string`, required): Workspace that will own the channel. Must match the authenticated API key workspace.
- `provider` (`string`, required): Provider key such as `telegram` or `email`.
- `provider_account_id` (`string`, required): Provider account that authorizes sends for this channel.
- `destination` (`string`, required): Provider-specific target, such as a Telegram chat id or email address.
- `metadata` (`object<string,string>`, optional, default `{}`): Additional routing metadata used by future mapping or policy decisions.

### Example Request JSON
```json
{
  "workspace_id": "ws_abc123",
  "provider": "telegram",
  "provider_account_id": "pa_telegram_ops",
  "destination": "-1001234567890",
  "metadata": {
    "purpose": "ops-alerts"
  }
}
```

## 4. Response
### Success (`201 Created`)
```json
{
  "id": "ch_5a5f6e7e7d4f4eb4b8d4a5d7",
  "workspace_id": "ws_abc123",
  "provider": "telegram",
  "provider_account_id": "pa_telegram_ops",
  "destination": "-1001234567890",
  "metadata": {
    "purpose": "ops-alerts"
  },
  "is_active": true,
  "created_at": "2026-04-16T10:15:00+00:00"
}
```

### Error Responses
- `400 Bad Request`: Invalid provider, invalid destination, or invalid provider-account configuration.
- `403 Forbidden`: Authenticated API key does not belong to `workspace_id`.
- `404 Not Found`: Workspace or provider account does not exist.
- `409 Conflict`: Route configuration conflicts with an existing managed channel.
- `422 Unprocessable Entity`: Request schema invalid.

## 5. Internal Processing Flow After Request
1. Validate request body and authenticated API key.
2. Enforce that `request.workspace_id` matches `auth.workspace_id`.
3. `CreateManagedChannelUseCase` validates workspace and provider-account existence.
4. Provider configuration validator checks that the provider and account combination is valid.
5. Use case creates a managed `Channel` entity and persists it.
6. Audit metadata is recorded for operational traceability.
7. Route returns a transport-safe channel projection.

## 6. What To Do Next
- Use `GET /channels?workspace_id=...` to verify the workspace routing table.
- Use `PATCH /channels/{channel_id}` to disable the route when it should stop receiving events.
- Use `/notifications/send` or `/events` to fan out through this channel.
