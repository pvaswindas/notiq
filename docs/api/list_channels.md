# List Channels API

## 1. Endpoint and Method
- Method: `GET`
- Path: `/workspaces/{workspace_id}/channels`
- Handler: `ChannelControllerFactory.list_channels`

## 2. Headers
- `Content-Type: application/json` (recommended)
- `Authorization`: not required by current route implementation.

## 3. Request Payload
- None.
- Path parameter:
  - `workspace_id` (`string`, required): Workspace identifier.

### Example Request
```http
GET /workspaces/ws_f47ac10b58cc4372a5670e02/channels HTTP/1.1
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
[
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
]
```

### Error Responses
- `400 Bad Request`: Blank workspace_id.
- `404 Not Found`: Workspace does not exist.

## 5. Internal Processing Flow After Request
1. Validate workspace ID.
2. Verify workspace exists.
3. Load channels scoped to workspace.
4. Map channel domain entities to API response.

## 6. What To Do Next
- Use channel IDs to target `/notifications/send` with `channel_ids`.
- Update or disable channels as needed.
