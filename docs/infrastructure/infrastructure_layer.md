# Infrastructure Layer

## Database Design
### Primary Tables
- `workspaces`: tenant identity and activation state.
- `channels`: workspace routing configuration.
- `provider_accounts`: structured provider credentials, activation, and default scopes.
- `delivery_jobs`: queue, routing snapshot, persisted event payload, and execution lifecycle data.
- `idempotency_keys`: dedupe claims.
- `api_keys`: bearer-key authentication records.
- `admins`: administrative user accounts.
- `roles`: named RBAC roles.
- `permissions`: named RBAC permissions.
- `admin_roles`: admin-role association table.
- `role_permissions`: role-permission association table.
- `rate_limit_configs`: runtime delivery throttling overrides.
- `audit_logs`: before-and-after operational trace records.

### Key Integrity And Performance Concerns
- Unique dedupe key behavior prevents duplicate channel work creation.
- Claim paths rely on indexes for due-job scans and lease recovery.
- Foreign keys preserve tenant and resource consistency.
- `provider_accounts.credentials` is JSONB so providers can evolve credential shape without repeated schema churn.
- `delivery_jobs.event_payload` is JSONB so workers can retry from persisted context.

Schema evolution is managed through Alembic migrations in `alembic/versions`.

## Queue And Job Processing
### Primary Processing Model
- Delivery queue semantics are represented by rows in `delivery_jobs`.
- Workers claim jobs with lease metadata and process them asynchronously.
- Concurrency safety relies on transactional row locking.

### Worker Behavior
- Delivery execution logic is split between `NotificationWorker` and `ProcessDeliveryJobUseCase`.
- The supported notification worker runtime is `python -m src.run_worker`.
- Workers claim jobs in batches and use a lease to recover from crashes or stuck executions.
- Rate-limit deferrals are persisted as future-due `PENDING` jobs rather than sleeping inside the worker.

## External Integrations
- Provider adapters: Telegram and Email senders.
- Database adapters: SQLAlchemy async repositories for notification, auth, RBAC, audit, and rate-limit data.
- Redis adapters: delivery rate limiting and shared runtime concerns.
- JWT signing and verification via `PyJWT` in `AdminAuthService`.

## Deployment Setup
### Docker Compose Services
- `postgres`
- `redis`
- `app` (FastAPI runtime)
- `worker` (notification worker runtime)

### Environment Variables
- `DATABASE_URL`
- `REDIS_URL`
- `APP_MODE`
- `WORKER_ID`
- `WORKER_BATCH_SIZE`
- `WORKER_POLL_INTERVAL_SECONDS`
- `WORKER_LEASE_SECONDS`
- `MAX_EVENTS_PER_MINUTE`
- `DELIVERY_WORKSPACE_RATE_LIMIT_PER_MINUTE`
- `DELIVERY_CHANNEL_RATE_LIMIT_PER_MINUTE`
- `DELIVERY_RATE_LIMIT_WINDOW_SECONDS`
- `DELIVERY_RATE_LIMIT_BACKOFF_SECONDS`
- `IDEMPOTENCY_TTL_SECONDS`
- `ADMIN_JWT_SECRET`
- `ADMIN_JWT_ALGORITHM`
- `ADMIN_JWT_EXP_MINUTES`

## Extension Rules
1. Keep transaction and locking guarantees intact when modifying claim or update logic.
2. Keep all infrastructure behavior behind ports or explicit adapter boundaries.
3. Document schema, index, retry, and operational changes in docs and migrations.
4. Keep admin auth and RBAC persistence behavior aligned with endpoint docs.
5. When adding provider-specific fields, prefer JSON payload evolution plus validation over proliferating special-purpose columns.
