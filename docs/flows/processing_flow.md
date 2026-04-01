# Processing Flow (Asynchronous Delivery Execution)

## Purpose
Describe how persisted `delivery_jobs` are claimed, executed, retried, and finalized.

## Step-By-Step Flow
1. Worker requests claimable jobs (`claim_due_jobs`) with lease metadata.
2. Repository selects jobs that are:
   - `PENDING` and due (`next_retry_at` null or elapsed), or
   - `PROCESSING` with expired lease.
3. Selection uses row locking (`FOR UPDATE SKIP LOCKED`) for concurrent safety.
4. Claimed jobs are updated to `PROCESSING` with owner + lease expiration.
5. `ProcessDeliveryJobUseCase.execute(job)` runs per claimed job.
6. Use case validates provider account availability.
7. Sender registry resolves sender implementation by provider key.
8. Sender attempts provider delivery.
9. Use case persists one of three outcomes:
   - `SUCCESS`: clear processing metadata, clear error/retry schedule.
   - Retryable `PENDING`: increment retry count, compute `next_retry_at = now + 2**retry_count`.
   - Terminal `FAILED`: capture error and clear processing metadata.

## Internal Decisions
### Retry Classification
- Transient classes: `TimeoutError`, `ConnectionError`, `OSError`.
- Any other exception is considered non-transient and may terminate immediately.

### Retry Budget
- Retries continue while transient and `retry_count < max_retries`.
- On terminal failure path, retry count is capped at `max_retries`.

### Lease Ownership
- Processing ownership fields are always cleared when a job is persisted as `SUCCESS`, retryable `PENDING`, or `FAILED`.

## Failure Handling
- Worker crash after claim: lease expiration makes job reclaimable.
- Sender misconfiguration/unknown provider: persisted as retryable or terminal based on classification.
- Infrastructure outage during update: job state remains unchanged and is retried by subsequent claims.

## Operational Guarantees
- At-least-once execution semantics.
- No exactly-once guarantee across provider boundaries.
- External providers should remain idempotent where feasible.
