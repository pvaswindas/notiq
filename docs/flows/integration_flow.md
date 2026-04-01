# Integration Flow

## Purpose
Describe how API boundaries, persistence, queues, auth, and provider integrations connect to application use cases.

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
- Action: request schema + auth context -> legacy `ProcessEventUseCase`.

### Workspace/Channel/API-Key Management Endpoints
- Adapters: `WorkspaceControllerFactory`, `ChannelControllerFactory`, `ApiKeyControllerFactory`.
- API-key endpoints and `/events` enforce workspace-aware API key auth.

## Outbound Integrations
### Databases
- PostgreSQL stores workspaces, channels, api keys, provider accounts, delivery jobs, idempotency keys.
- SQLAlchemy async repositories implement persistence ports.

### Queueing
- Primary modular flow: Postgres table-backed queue semantics (`delivery_jobs` claims).
- Compatibility flow: Celery + Redis broker/backend.

### Idempotency and Throttling
- Primary modular flow: idempotency claims persisted in Postgres-backed repository.
- Compatibility `/events` flow: Redis idempotency keys + Redis rate limiter.

### Provider Delivery
- Sender registry resolves provider sender adapters (Telegram, Email).
- Provider credentials are resolved through provider-account abstractions.

## Routing Logic Across Layers
1. Adapter validates and maps protocol input.
2. Use case orchestrates policy and routing decisions.
3. Ports abstract required side effects.
4. Infrastructure adapters execute I/O.
5. Adapter maps outcome to HTTP response or persisted lifecycle state.

## Boundary Failure Handling
- Auth failures return `401`/`403` at dependency layer.
- Validation failures return `422` from FastAPI/Pydantic.
- Known business validation in compatibility routes maps to `400`/`404`.
- Provider and network failures enter retry/terminal policy logic in job execution or Celery retry behavior.

## Extension Guardrails
1. Add integration behavior behind ports first.
2. Keep auth/payload/persistence semantics documented in endpoint files under `docs/api`.
3. Update this flow doc when routing or external dependency ownership changes.
