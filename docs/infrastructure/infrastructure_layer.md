# Infrastructure Layer

## Database Design

### Core Tables
- `workspaces`: tenant identity and activation state.
- `provider_accounts`: provider credential references and default scopes.
- `channels`: workspace routing destinations and provider bindings.
- `delivery_jobs`: durable queue + execution lifecycle state.
- `idempotency_keys`: claimed dedupe keys for duplicate suppression.

### Critical Constraints and Indexes
- Unique `delivery_jobs.dedupe_key` ensures one job per dedupe fingerprint.
- Worker-claim indexes support due-job scans (`status`, `next_retry_at`, `processing_expires_at`).
- Foreign keys enforce workspace/channel/account integrity.

Migration source: `alembic/versions/0001_init.py`.

## Queue and Job Processing Systems

### Primary Queue Model (Postgres-backed)
- Queue is represented by `delivery_jobs` rows in `PENDING` status.
- Workers lease jobs by atomically updating claim fields.
- `FOR UPDATE SKIP LOCKED` enables safe multi-worker concurrency.

### Legacy Queue Model (Celery)
- `/events` compatibility path enqueues Celery tasks.
- Broker/backend configured via Redis in `src/infrastructure/celery_app.py`.
- Task implementation located at `src/adapters/tasks/send_notification_task.py`.

## Worker Behavior

### Primary Worker Class
`NotificationWorker`:
- Polls claimed batches at configured interval.
- Delegates transition logic to `ProcessDeliveryJobUseCase`.
- Logs unexpected exceptions per job context.

### Runtime Status
Primary worker class exists and is production-ready in code, but default local startup path uses API process + Celery worker service in `docker-compose.yml`.

## External Integrations

### Provider Integrations (Primary)
- Telegram sender adapter
- Email sender adapter

Both adapters consume `ProviderAccount.credentials_ref` and are resolved by provider key through sender registry.

### Redis Integrations (Legacy)
- Celery broker/backend transport.
- Redis idempotency store used by legacy Celery task flow.

## Deployment Setup

### Docker Compose Services
- `postgres`: Postgres 16 with persistent volume and healthcheck.
- `redis`: Redis 7 for Celery broker/backend and legacy idempotency.
- `app`: FastAPI process (`python -m src.run`).
- `worker`: Celery worker process (`celery -A src.infrastructure.celery_app.celery_app worker`).

### Environment Variables
Key variables from `.env.example` / `settings.py`:
- `DATABASE_URL`
- `REDIS_URL`
- `APP_MODE`
- `WORKER_ID`
- `WORKER_BATCH_SIZE`
- `WORKER_POLL_INTERVAL_SECONDS`
- `WORKER_LEASE_SECONDS`
- `MAX_EVENTS_PER_MINUTE`
- `IDEMPOTENCY_TTL_SECONDS`

## Infrastructure Extension Rules
1. Preserve transaction boundaries and atomicity for claim/update flows.
2. Do not bypass repository ports from use cases.
3. Keep schema and migration docs synchronized with model changes.
4. Document operational impact for any retry, lease, or index change.
