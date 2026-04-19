# Processing Flow (Asynchronous Delivery Execution)

## Purpose
Describe how persisted `delivery_jobs` are claimed, executed, deferred, retried, and finalized.

## Step-By-Step Flow
1. Worker requests claimable jobs (`claim_due_jobs`) with lease metadata.
2. Repository selects jobs that are:
   - `PENDING` and due (`next_retry_at` null or elapsed), or
   - `PROCESSING` with expired lease.
3. Selection uses row locking (`FOR UPDATE SKIP LOCKED`) for concurrent safety.
4. Claimed jobs are updated to `PROCESSING` with owner and lease expiration.
5. `ProcessDeliveryJobUseCase.execute(job)` runs once per claimed job.
6. The use case validates that the job still points to an active provider account in the same workspace and for the same provider.
7. `DeliverySafetyService` checks workspace, channel, provider, and global rate-limit policy before any provider call.
8. If a limit is exceeded, the job is deferred back to `PENDING` with `next_retry_at = now + delivery_rate_limit_backoff_seconds`.
9. If allowed, sender registry resolves the sender implementation by provider key.
10. Sender attempts provider delivery using:
    - a synthetic `Channel` built from job routing fields, and
    - the persisted `job.event_payload`.
11. Use case persists one of three outcomes:
    - `SUCCESS`: clear processing metadata, clear error and retry schedule.
    - Retryable `PENDING`: increment retry count and compute `next_retry_at = now + 2**retry_count`.
    - Terminal `FAILED`: capture error and clear processing metadata.

## Internal Decisions
### Retry Classification
- `httpx.HTTPStatusError` is retryable only for `429` and `5xx`.
- `httpx.RequestError`, `TimeoutError`, `ConnectionError`, and `OSError` are retryable.
- Most validation or configuration failures are terminal because they will not improve on retry.

### Retry Budget
- Retries continue while the error is transient and `retry_count < max_retries`.
- On terminal failure path, retry count is capped at `max_retries`.

### Lease Ownership
- Processing ownership fields are always cleared when a job is persisted as `SUCCESS`, retryable `PENDING`, deferred `PENDING`, or `FAILED`.

## Failure Handling
- Worker crash after claim: lease expiration makes job reclaimable.
- Sender misconfiguration, missing provider account, or provider mismatch: terminal failure because these are not transient conditions.
- Provider throttling detected by `DeliverySafetyService`: job is deferred without incrementing retry count.
- Infrastructure outage during update: job state may remain unchanged and can be reclaimed after lease expiration.

## Operational Guarantees
- At-least-once execution semantics.
- No exactly-once guarantee across provider boundaries.
- External providers should remain idempotent where feasible.
