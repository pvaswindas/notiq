# Admin Login API

## 1. Endpoint and Method
- Method: `POST`
- Path: `/admin/auth/login`
- Handler: `AdminControllerFactory.login`

## 2. Headers
- `Content-Type: application/json` (required)
- `Authorization`: not required.

## 3. Request Payload

### Body Schema
- `email` (`string`, required, min 3, max 255): Admin email address.
- `password` (`string`, required, min 1, max 256): Plaintext password validated by bcrypt.

### Example Request JSON
```json
{
  "email": "admin@example.com",
  "password": "StrongPassword123"
}
```

## 4. Response
### Success (`200 OK`)
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_at": "2026-04-01T20:30:00+00:00",
  "admin_id": "adm_01",
  "roles": ["platform-admin"]
}
```

### Error Responses
- `400 Bad Request`: Missing email or password.
- `401 Unauthorized`: Invalid credentials.
- `403 Forbidden`: Admin exists but is disabled.
- `422 Unprocessable Entity`: Invalid request schema.

## 5. Internal Processing Flow After Request
1. Validate request schema.
2. Normalize email (`strip().lower()`).
3. Load admin by email.
4. Verify password hash.
5. Ensure admin is active.
6. Resolve role names assigned to admin.
7. Sign JWT with admin id, roles, and expiration.
8. Return token payload.

## 6. What To Do Next
- Use returned JWT as `Authorization: Bearer <token>` for `/admin/*` endpoints.
- Renew token by re-authenticating after expiration.
