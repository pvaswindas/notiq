# Design Principles

## Reliability Over Immediate Delivery
### Why
Provider APIs are inherently unreliable and should not control API response latency.

### How
- API path persists work as delivery jobs.
- Worker execution handles retries and terminal failure transitions.

### Constraint
`200 OK` means "accepted for processing", not "delivered".

## Deterministic Idempotency
### Why
Upstream callers retry requests; duplicate sends must be prevented per destination.

### How
- Event fingerprint: deterministic hash of event context.
- Channel fingerprint: deterministic hash of `(event_fingerprint, channel_id)`.
- Atomic claim in `idempotency_keys` table blocks duplicate job creation.

### Constraint
Payload canonicalization and fingerprint inputs must remain stable across deployments.

## Tenant Isolation
### Why
Workspaces must never leak channels, credentials, or job processing context across tenants.

### How
- Workspace-scoped queries for channel resolution.
- Workspace-bound job and provider-account relationships.
- Workspace context carried through job execution and logs.

### Constraint
All new routing/persistence features must preserve workspace boundaries by default.

## Replaceable Integrations
### Why
Provider and storage technology choices evolve over time.

### How
- Use cases depend on ports.
- Concrete adapters are selected in container wiring.
- Domain entities remain persistence and framework agnostic.

### Constraint
Integration changes should be achievable without modifying domain policy code.

## Explicit Failure Semantics
### Why
Operational teams need predictable lifecycle behavior under failure.

### How
- Status model: `PENDING`, `PROCESSING`, `SUCCESS`, `FAILED`.
- Transient errors retry with exponential backoff.
- Permanent errors move to terminal failure state with captured error context.

### Constraint
Any new status or retry policy must include migration and documentation updates.

## Bounded Throughput Protection (Legacy Compatibility)
### Why
Legacy Celery fan-out can burst provider traffic and create avoidable throttling incidents without local controls.

### How
- Resolve effective policy in order: group -> provider -> tenant -> global.
- Enforce counters atomically in Redis using fixed-window semantics.
- On throttle deny, release idempotency key and requeue task with short delay.

### Constraint
Throttle controls are compatibility safeguards for `/events`; primary architecture evolution should continue in modular notifications flow.
