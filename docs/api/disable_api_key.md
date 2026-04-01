# Disable API Key API

## 1. Endpoint and Method
- Method: `PATCH`
- Path: `/api-keys/{api_key_id}/disable`
- Handler: `ApiKeyControllerFactory.disable_api_key`

## 2. Headers
- `Content-Type: application/json` (recommended)
- `Authorization: Bearer <api_key>` (required)

## 3. Request Payload
- None.
- Path parameter:
  - `api_key_id` (`string`, required): API key record identifier.

### Example Request
```http
PATCH /api-keys/key_43a0fae6730f4f6d9235f2ea/disable HTTP/1.1
Host: localhost:8000
Authorization: Bearer notiq_xxx
```

### Example Request JSON (Path Parameters)
```json
{
  "api_key_id": "key_43a0fae6730f4f6d9235f2ea"
}
```

## 4. Response
### Success (`200 OK`)
```json
{
  "id": "key_43a0fae6730f4f6d9235f2ea",
  "is_active": false
}
```

### Error Responses
- `401 Unauthorized`: Missing/malformed authorization header.
- `403 Forbidden`: Invalid/disabled auth key or cross-workspace disable attempt.
- `404 Not Found`: API key not found.

## 5. Internal Processing Flow After Request
1. Authenticate request.
2. Load target API key by ID.
3. Enforce same-workspace ownership.
4. Persist `is_active=false`.
5. Return minimal disable response.

## 6. What To Do Next
- Update clients using the disabled key.
- Verify no critical traffic still depends on that credential.
