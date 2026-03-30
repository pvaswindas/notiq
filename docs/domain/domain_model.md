# Domain Model

## Domain Scope
The primary domain model for production notification orchestration lives under `src/modules/notifications/domain`.

A separate legacy event model exists under `src/domain` for compatibility ingestion (`POST /events`).

## Entities (Primary Notifications Domain)

### Workspace
Why it exists:
- Defines tenant boundary and activation gate for notification intake.

What problem it solves:
- Prevents cross-tenant routing and allows tenant lifecycle control (`is_active`).

How it interacts:
- Parent context for channels and delivery jobs.
- Checked by `SendNotificationUseCase` before any queueing.

### Channel
Why it exists:
- Represents a notification route from workspace to provider destination.

What problem it solves:
- Allows configurable fan-out per workspace and destination.

How it interacts:
- Selected during intake routing.
- Supplies `provider_key`, destination, and optional explicit account.
- One channel can generate many delivery jobs over time.

### ProviderAccount
Why it exists:
- Represents credential reference for outbound provider calls.

What problem it solves:
- Separates credential ownership and default resolution from channel/event payloads.

How it interacts:
- Resolved per channel by `ProviderAccountResolver`.
- Used by sender adapters during delivery execution.
- Can be workspace-scoped default or system default fallback.

### Event
Why it exists:
- Captures immutable event context from intake request.

What problem it solves:
- Provides stable input for message mapping and idempotency fingerprinting.

How it interacts:
- Input to idempotency service and message mapper.
- Combined with channel to create delivery jobs.

### DeliveryJob
Why it exists:
- Durable executable unit for asynchronous processing.

What problem it solves:
- Decouples API acceptance from external provider latency and failure.

How it interacts:
- Persisted by intake use case.
- Claimed and transitioned by worker processing use case.
- Tracks retries, lease ownership, and terminal outcome.

## Relationships (Primary)
- `Workspace 1 -> N Channel`
- `Workspace 1 -> N DeliveryJob`
- `Channel 1 -> N DeliveryJob`
- `ProviderAccount 1 -> N DeliveryJob` (resolved reference)
- `ProviderAccount 0..1 <- Channel` (optional explicit account)

## Value Objects and Services
- `EventFingerprint`: typed wrapper around deterministic event hash.
- `ProviderKey`: normalized provider identifier value object.
- `IdempotencyService`: computes deterministic event and channel fingerprints.
- `RateLimitService`: policy utility present in domain but not currently applied in primary intake flow.

## Legacy Domain (Compatibility)
Legacy entities `src/domain/entities/event.py` and `src/domain/entities/channel.py` are used by `/events` ingestion and Celery task routing.

These models are intentionally minimal and should not be used for new primary notification features.
