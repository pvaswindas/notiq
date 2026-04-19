# Admin Disable Workspace API

## 1. Endpoint and Method
- Method: `PATCH`
- Path: `/admin/workspaces/{workspace_id}/disable`
- Handler: `AdminControllerFactory.disable_workspace`

## 2. Headers
- `Authorization: Bearer <admin_jwt>` (required)
- `Content-Type: application/json` is not required because the route has no body.

## 3. Request Payload
- Path parameter:
  - `workspace_id` (`string`, required): Workspace to disable.

### Authorization Requirement
- Caller must have the `manage_workspaces` permission.

## 4. Response
### Success (`200 OK`)
```json
{
  "id": "ws_abc123",
  "name": "Operations Workspace",
  "is_active": false,
  "created_at": "2026-04-01T08:30:00+00:00"
}
```

### Error Responses
- `400 Bad Request`: Invalid workspace identifier.
- `401 Unauthorized`: Missing or invalid admin token.
- `403 Forbidden`: Authenticated admin lacks `manage_workspaces`.
- `404 Not Found`: Workspace does not exist.

## 5. Internal Processing Flow After Request
1. Decode and authorize the admin JWT.
2. `DisableWorkspaceUseCase` validates the input.
3. The workspace is loaded and transitioned to inactive state.
4. Audit metadata marks the action source as `admin`.
5. Response returns the updated workspace projection.

## 6. What To Do Next
- Expect future notification intake for that workspace to fail validation.
- Review channels and provider accounts only if you are planning later reactivation or tenant offboarding.
