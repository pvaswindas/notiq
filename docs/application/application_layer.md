# Application Layer

## Scope
The primary application layer lives in `src/modules/notifications/application` and orchestrates notification intake and job processing.

A smaller legacy use case exists in `src/application/use_cases/process_event_use_case.py` for compatibility endpoint `/events`.

## Primary Use Cases

### SendNotificationUseCase
Purpose:
- Convert inbound notification request into persisted, deduplicated delivery jobs.

Key orchestration decisions:
1. Validate required command identity fields.
2. Validate workspace existence and active status.
3. Load active channels and apply optional channel filter.
4. Resolve provider account per channel.
5. Generate and claim channel dedupe key.
6. Persist delivery job for successful claims.
7. Return enqueue summary.

Important constraints:
- No direct infrastructure or SDK logic.
- Idempotency is channel-level.
- Explicit misconfigured account fails fast for that channel path.

### ProcessDeliveryJobUseCase
Purpose:
- Execute a claimed job and persist lifecycle transitions.

Key orchestration decisions:
1. Validate provider account availability.
2. Resolve sender by provider key.
3. Execute send attempt.
4. Classify error as transient or permanent.
5. Persist `SUCCESS`, retryable `PENDING`, or terminal `FAILED`.

Important constraints:
- Must clear lease ownership fields on completion path.
- Retry policy remains centralized in this use case.

## Application Services

### ProviderAccountResolver
- Encapsulates account fallback policy.
- Prevents account-selection logic from leaking into use cases.

### SenderRegistry
- Maps provider key to outbound sender implementation.
- Centralizes unsupported-provider handling.

### EventMessageMapper
- Converts event/channel context into deterministic message text.
- Keeps formatting logic out of use case orchestration.

## Legacy Application Flow
`ProcessEventUseCase` in `src/application/use_cases` loads active channels and enqueues Celery tasks.

Use this flow only for compatibility behavior; new orchestration should be added to modular notifications application layer.
