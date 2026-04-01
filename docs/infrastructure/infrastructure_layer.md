# Infrastructure Layer

## Database Design

### Primary Tables
- `workspaces`: tenant identity + activation state.
- `channels`: workspace routing configuration.
- `provider_accounts`: provider credentials references and default scopes.
- `delivery_jobs`: queue + execution lifecycle data.
- `idempotency_keys`: dedupe claims.
- `api_keys`: bearer-key authentication records.
- `admins`: administrative user accounts.
- `roles`: named RBAC roles.
- `permissions`: named RBAC permissions.
- `admin_roles`: admin-role association table.
- `role_permissions`: role-permission association table.

### Key Integrity and Performance Concerns
- Unique dedupe key behavior prevents duplicate channel work creation.
- Claim paths rely on indexes for due-job scans and lease recovery.
- FK constraints preserve tenant/resource consistency.

Schema evolution is managed via Alembic migrations in `alembic/versions`.

## Queue and Job Processing

### Primary Processing Model
- Delivery queue is represented by rows in `delivery_jobs`.
- Workers claim with lease semantics and process asynchronously.
- Concurrency safety relies on transactional row locking.

### Compatibility Processing Model
- `/events` enqueues Celery tasks.
- Redis provides broker/backend transport.
- Task-level idempotency and throttling controls are Redis-backed.

## Worker Behavior
- Modular flow execution logic is in `ProcessDeliveryJobUseCase` and worker orchestration classes.
- Compatibility worker runtime is Celery-based (`src.infrastructure.celery_app`).
- Deprecated worker entrypoints remain only to fail-fast with guidance.

## External Integrations
- Provider adapters: Telegram and Email senders.
- Database adapters: SQLAlchemy async repositories for domain and auth data.
- Redis adapters: Celery transport, compatibility idempotency store, compatibility rate limiter.
- JWT signing/verification via `PyJWT` in `AdminAuthService`.

## Deployment Setup

### Docker Compose Services
- `postgres`
- `redis`
- `app` (FastAPI runtime)
- `worker` (Celery worker runtime)

### Environment Variables
- `DATABASE_URL`
- `REDIS_URL`
- `APP_MODE`
- `WORKER_ID`
- `WORKER_BATCH_SIZE`
- `WORKER_POLL_INTERVAL_SECONDS`
- `WORKER_LEASE_SECONDS`
- `MAX_EVENTS_PER_MINUTE`
- `IDEMPOTENCY_TTL_SECONDS`
- `ADMIN_JWT_SECRET`
- `ADMIN_JWT_ALGORITHM`
- `ADMIN_JWT_EXP_MINUTES`

## Extension Rules
1. Keep transaction and locking guarantees intact when modifying claim/update logic.
2. Keep all infrastructure behavior behind ports or explicit adapter boundaries.
3. Document schema/index, retry, and operational changes in docs + migrations.
4. Keep admin auth and RBAC persistence behavior aligned with endpoint docs.
