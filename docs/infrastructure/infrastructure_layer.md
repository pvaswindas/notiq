# Infrastructure Layer

## Postgres Usage
Tables:
- `workspaces`
- `provider_accounts`
- `channels`
- `delivery_jobs`
- `idempotency_keys`

Persistence adapters implement ports and map ORM models to immutable domain entities.

Key patterns:
- `idempotency_keys` insertion with unique key for atomic duplicate prevention.
- `delivery_jobs` status/lease indexes for worker claim performance.

## Queue Mechanism
Notiq uses a durable database-backed queue pattern through `delivery_jobs` rather than a broker.

Queue semantics implemented by repository:
- `PENDING` jobs represent queued work.
- `claim_due_jobs` atomically leases due jobs with `FOR UPDATE SKIP LOCKED`.
- lease timeout allows recovery from worker crashes.

## Worker Design
- Worker process is started when `APP_MODE=worker`.
- Infinite polling loop with configurable:
  - `WORKER_BATCH_SIZE`
  - `WORKER_POLL_INTERVAL_SECONDS`
  - `WORKER_LEASE_SECONDS`
- Delegates business transitions to `ProcessDeliveryJobUseCase`.

## Docker Setup
`docker-compose.yml` defines three services:
1. `postgres` (persistent volume + healthcheck)
2. `app` (API process, `APP_MODE=api`, exposes `8000`)
3. `worker` (background processor, `APP_MODE=worker`)

`Dockerfile` builds a Python 3.12 slim image and runs `python -m src.run`.
