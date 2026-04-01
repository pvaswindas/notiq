# Domain Model

## Scope
The canonical production domain for notifications lives under `src/modules/notifications/domain`.

Compatibility domain objects exist under `src/domain` and are maintained only for legacy route/task behavior.

## Primary Entities

### Workspace
Why it exists:
- Defines tenant boundary and activation gate.

What problem it solves:
- Ensures all routing and execution are scoped to a tenant context.

How it interacts:
- Parent context for channels, provider-account defaults, and delivery jobs.

### Channel
Why it exists:
- Represents a delivery route configuration owned by a workspace.

What problem it solves:
- Separates destination/provider configuration from event payloads.

How it interacts:
- Selected during fan-out.
- Supplies provider key, destination, and optional explicit provider account.

### ProviderAccount
Why it exists:
- Encapsulates provider credential ownership and activation status.

What problem it solves:
- Enables credential rotation and defaulting without mutating channels/events.

How it interacts:
- Resolved per channel by `ProviderAccountResolver`.
- Used during send execution by outbound sender adapters.

### Event
Why it exists:
- Holds immutable event identity and payload used by intake orchestration.

What problem it solves:
- Provides stable input for message mapping and fingerprint computation.

How it interacts:
- Combined with channels to generate channel-scoped delivery work.

### DeliveryJob
Why it exists:
- Durable executable unit for asynchronous provider delivery.

What problem it solves:
- Decouples API acceptance from provider latency and failure modes.

How it interacts:
- Created in intake use case.
- Claimed and transitioned by processing use case.
- Tracks retries, lease ownership, and final state.

## Relationships
- `Workspace 1 -> N Channel`
- `Workspace 1 -> N DeliveryJob`
- `Channel 1 -> N DeliveryJob`
- `ProviderAccount 1 -> N DeliveryJob`
- `ProviderAccount 0..1 <- Channel` (optional explicit binding)

## Value Objects and Domain Services
- `ProviderKey`: normalizes provider identity.
- `EventFingerprint`: typed representation of deterministic event hash.
- `IdempotencyService`: creates event and channel fingerprints.

## Compatibility Domain Notes
Legacy `/events` flow uses:
- `src/domain/entities/event.py`
- `src/domain/entities/channel.py`
- `src/domain/rate_limit/entities.py`

These are compatibility models and must not become the default modeling target for new primary notification capabilities.
