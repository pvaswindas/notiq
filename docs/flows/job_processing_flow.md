# Job Processing Flow

## How Jobs Are Created
1. `SendNotificationUseCase` computes a channel-scoped dedupe key.
2. If dedupe key is newly claimed, it creates a `DeliveryJob` entity.
3. Job is saved to Postgres with `PENDING` status.

## How Workers Claim Jobs
1. Worker loop calls `claim_due_jobs(worker_id, limit, lease_seconds)`.
2. Repository selects jobs that are:
- `PENDING` and retry time is due (or no retry time), or
- `PROCESSING` with expired lease (`processing_expires_at <= now`).
3. Query uses `FOR UPDATE SKIP LOCKED` to avoid double-claim across workers.
4. Claimed jobs are marked `PROCESSING` with owner + lease expiration.

## Retry Logic
1. Worker executes `ProcessDeliveryJobUseCase.execute(job)`.
2. On transient exception (`TimeoutError`, `ConnectionError`, `OSError`) and retry budget available:
- Increment `retry_count`.
- Compute backoff as `2 ** retry_count` seconds.
- Set `next_retry_at`.
- Move status back to `PENDING`.
3. Worker loop later reclaims the job after `next_retry_at`.

## Failure Handling
### Permanent failure path
A job becomes `FAILED` when:
- Error is non-transient, or
- Retry budget exhausted (`retry_count >= max_retries`)

### State updates on failure
- Status -> `FAILED`
- Error string truncated to storage-safe length
- Lease ownership fields cleared

### Success path
- Status -> `SUCCESS`
- Error and lease fields cleared
- `next_retry_at` cleared

## Lease Safety
Lease fields prevent stuck jobs:
- If worker crashes after claim, lease expires.
- Another worker can reclaim expired `PROCESSING` job.
