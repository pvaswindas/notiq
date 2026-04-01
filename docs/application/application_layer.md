# Application Layer

## Scope
Primary orchestration for notifications is implemented in `src/modules/notifications/application`.

A compatibility orchestration path remains in `src/application/use_cases/process_event_use_case.py` for the legacy `/events` endpoint.

## Primary Use Cases

### SendNotificationUseCase
What it does:
- Converts one inbound command into deduplicated persisted delivery jobs.

Decision flow:
1. Validate required command identifiers.
2. Validate workspace exists and is active.
3. Resolve active channels and apply optional `channel_ids` filter.
4. Resolve provider account per channel.
5. Compute/claim channel-level idempotency key.
6. Persist new delivery jobs for successful claims.
7. Return enqueue summary.

Important constraints:
- No direct dependency on concrete infrastructure classes.
- Per-channel dedupe behavior is intentional.

### ProcessDeliveryJobUseCase
What it does:
- Executes one claimed job and persists lifecycle transition.

Decision flow:
1. Validate provider account availability.
2. Resolve sender by provider key.
3. Attempt send.
4. Classify exception as transient/non-transient.
5. Persist `SUCCESS`, retryable `PENDING`, or terminal `FAILED`.

Important constraints:
- Lease ownership fields must be cleared on persisted outcomes.
- Retry schedule remains centralized here.

## Application Services
### ProviderAccountResolver
- Encapsulates account fallback order and validation.

### SenderRegistry
- Central lookup for provider key -> sender implementation.

### EventMessageMapper
- Produces deterministic text payloads for delivery jobs.

## Compatibility Application Behavior
Legacy `ProcessEventUseCase` fans out channels into Celery tasks.

Associated compatibility services (for example rate-limit resolution) remain valid only for `/events` behavior and should not absorb new primary architecture work.
