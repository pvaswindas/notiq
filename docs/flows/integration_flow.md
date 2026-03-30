# Integration Flow

## Scope
This document explains integration points and routing between core logic and external systems.

## Inbound Integrations
### `POST /notifications/send`
- Adapter: `NotificationRouterFactory`
- Contract: `SendNotificationRequest`
- Action: map HTTP payload to `SendNotificationCommand`
- Output: enqueue summary response

### `POST /events` (Legacy Compatibility)
- Adapter: `EventRouterFactory`
- Contract: `EventIngestionRequest`
- Action: map event payload to legacy `ProcessEventUseCase`
- Output: `{"status": "accepted"}` on success
- Continuation: one Celery task per channel executes idempotency + rate-limit + provider send sequence

## Outbound Integrations
### Provider Senders
- Interface: `NotificationSenderPort`
- Implementations: Telegram, Email
- Routing: `SenderRegistry.resolve(provider_key)`
- Credentials source: `ProviderAccount.credentials_ref`

### Persistence
- SQLAlchemy async session per repository call.
- Tables used: `workspaces`, `channels`, `provider_accounts`, `delivery_jobs`, `idempotency_keys`.

### Queue/Broker
- Primary flow: Postgres-backed queue semantics via `delivery_jobs` claim model.
- Legacy flow: Celery + Redis broker/backend for event fan-out task execution.

### Legacy Rate-Limit Dependencies
- Resolver: `RateLimitResolver` selects group/provider/tenant/global config.
- Config source: `InMemoryRateLimitConfigRepository` (seeded defaults).
- Enforcement: `RedisRateLimiter` Lua-scripted atomic counter/expiry check.

## Internal Routing Logic
1. Inbound adapter maps protocol data to use-case command/entity.
2. Use case selects ports and orchestrates policy steps.
3. Port implementation executes I/O (database, provider, broker).
4. Results are mapped back to API response or persisted state transition.

## Failure Handling At Integration Boundaries
- Database write conflict on idempotency key: interpreted as duplicate event-channel attempt.
- Provider network failures: retried by job processing policy.
- Legacy Celery task failure: task autoretry and idempotency key release on exception.
- Legacy throttle deny: task requeues itself after releasing idempotency claim.

## Extension Guidance
To add a new integration safely:
1. Add or update a port contract only if existing contract cannot express required behavior.
2. Implement integration in adapter/infrastructure layer.
3. Register integration in composition root.
4. Update API/flow/development docs in the same change.
