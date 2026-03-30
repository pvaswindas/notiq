# Processing Flow

## Scope
This document covers asynchronous execution of persisted delivery jobs in the primary modular flow.

## Step-By-Step
1. `NotificationWorker` calls `claim_due_jobs(worker_id, limit, lease_seconds)`.
2. Repository selects claimable jobs:
   - `PENDING` jobs with `next_retry_at` due (or null), and
   - `PROCESSING` jobs whose lease expired.
3. Selection runs with `FOR UPDATE SKIP LOCKED` to avoid double claim between workers.
4. Claimed jobs are marked `PROCESSING` with `processing_owner` and `processing_expires_at` lease deadline.
5. Worker calls `ProcessDeliveryJobUseCase.execute(job)` per claimed job.
6. Use case loads provider account and validates it is active.
7. Sender registry resolves sender adapter by `provider_key`.
8. Sender attempts outbound delivery.
9. Use case persists outcome:
   - `SUCCESS` when send succeeds.
   - `PENDING` with incremented retry and `next_retry_at` when transient error and retry budget remain.
   - `FAILED` when non-transient error or retry budget exhausted.
10. Lease ownership fields are cleared on terminal update for each processed job.

## Retry Policy
- Transient error classes: `TimeoutError`, `ConnectionError`, `OSError`.
- Backoff formula: `2 ** retry_count` seconds after increment.
- `retry_count` is capped by `max_retries`.

## Failure Handling
### Worker Crash During Processing
Expired lease makes job reclaimable by another worker.

### Sender Misconfiguration
Missing or inactive provider account triggers failure path and state update with error context.

### Unknown Provider Key
Sender registry raises `ValueError`, resulting in retry/failed classification based on policy.

## Operational Behavior
This flow guarantees at-least-once processing for claimed jobs; provider integrations should remain idempotent where possible.
