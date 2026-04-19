# Integration Flow

## Purpose
Describe how API boundaries, persistence, queue semantics, auth, and provider integrations connect to application use cases.

## Inbound Integrations
### Primary Notifications Endpoint
- `POST /notifications/send`
- Adapter: `NotificationRouterFactory`
- Auth: currently no auth dependency in this route.
- Action: request schema -> command -> `SendNotificationUseCase`.

### Compatibility Event Endpoint
- `POST /events`
- Adapter: `EventRouterFactory`
- Auth: requires `Authorization: Bearer <api_key>`.
- Action: compatibility request and auth context -> `SendNotificationCommand` -> `SendNotificationUseCase`.

### Workspace And Management Endpoints
- Adapters: `WorkspaceControllerFactory`, `ProviderAccountControllerFactory`, `ChannelControllerFactory`, `ApiKeyControllerFactory`.
- Provider-account and channel endpoints require API-key auth and enforce workspace ownership through `AuthContext`.
- API-key endpoints and `/events` also enforce workspace-aware API key auth.

### Admin RBAC Endpoints
- Prefix: `/admin`
- Adapters: `AdminControllerFactory` and `AdminAuditControllerFactory`
- Auth:
  - `POST /admin/auth/login` is unauthenticated.
  - Most `/admin/*` routes require `Authorization: Bearer <admin_jwt>`.
  - Mutating or sensitive routes add permission guards through `require_permission(...)`.

## Outbound Integrations
### Databases
- PostgreSQL stores workspaces, channels, API keys, provider accounts, delivery jobs, idempotency keys, RBAC data, rate-limit configs, and audit logs.
- SQLAlchemy async repositories implement persistence ports.

### Queueing
- Queue semantics are modeled with Postgres-backed `delivery_jobs`.
- Worker concurrency safety relies on transactional row locking and leasing.

### Idempotency And Throttling
- Notification intake idempotency is persisted in the `idempotency_keys` table.
- Delivery throttling is enforced during job execution through `DeliverySafetyService` and `RedisDeliveryRateLimiter`.
- Admin-managed rate-limit configuration is stored in Postgres and read during safety checks.

### Provider Delivery
- Sender registry resolves provider sender adapters such as Telegram and Email.
- Provider credentials are resolved through provider-account abstractions and stored as structured JSON.
- Outbound senders receive the persisted event payload from the claimed job, not a reconstructed HTTP request.

## Routing Logic Across Layers
1. Adapter validates and maps protocol input.
2. Use case orchestrates policy and routing decisions.
3. Ports abstract required side effects.
4. Infrastructure adapters execute I/O.
5. Adapter maps the outcome to an HTTP response or persisted lifecycle state.

## Boundary Failure Handling
- Auth failures return `401` or `403` at the dependency layer.
- Validation failures return `422` from FastAPI and Pydantic.
- Known business validation in compatibility routes maps to `400` or `404`.
- The primary `/notifications/send` route currently leaves use-case failures unnormalized, so callers may see `500` for workspace or provider-account problems.
- Provider and network failures enter retry or terminal policy logic in `ProcessDeliveryJobUseCase`.
- Admin lifecycle and RBAC conflicts map to explicit API failures:
  - duplicate admin, role, or permission names -> `409`
  - missing admin, role, permission, or rate-limit config references -> `404`
  - insufficient permission grants -> `403`

## Extension Guardrails
1. Add integration behavior behind ports first.
2. Keep auth, payload, and persistence semantics documented in endpoint files under `docs/api`.
3. Update this flow doc when routing ownership or external dependency behavior changes.
