# Create Channel API

## 1. Endpoint and Method
- Method: `POST`
- Path: `/workspaces/{workspace_id}/channels`
- Handler: `ChannelControllerFactory.create_channel`

## 2. Headers
- `Content-Type: application/json` (required)
- `Authorization`: not required by current route implementation.

## 3. Request Payload

### Path Parameter
- `workspace_id` (`string`, required): Workspace to own the channel.

### Body Schema
- `provider` (`string`, required): Provider key (for example `telegram`, `email`).
- `config` (`object`, optional, default `{}`): Provider-specific configuration.
- `group` (`string | null`, optional): Optional grouping key for compatibility throttling contexts.
- `is_active` (`boolean`, optional, default `true`): Initial active state.

### Example Request JSON
```json
{
  "provider": "telegram",
  "config": {
    "chat_id": "12345"
  },
  "group": "priority-high",
  "is_active": true
}
```

## 4. Response
### Success (`201 Created`)
```json
{
  "id": "ch_5a5f6e7e7d4f4eb4b8d4a5d7",
  "workspace_id": "ws_f47ac10b58cc4372a5670e02",
  "provider": "telegram",
  "config": {
    "chat_id": "12345"
  },
  "group": "priority-high",
  "is_active": true
}
```

### Error Responses
- `400 Bad Request`: Missing/invalid workspace_id or provider.
- `404 Not Found`: Workspace does not exist.
- `422 Unprocessable Entity`: Request schema invalid.

## 5. Internal Processing Flow After Request
1. Validate path + body schema.
2. Validate target workspace exists.
3. Normalize and validate provider.
4. Construct channel domain object with generated ID.
5. Persist and return mapped response.

## 6. What To Do Next
- Use list/update/disable endpoints to manage lifecycle.
- Use `/notifications/send` or `/events` to fan out through this channel.
