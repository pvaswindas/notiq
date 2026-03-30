# Design Principles

## Multi-Tenant Design
### Why
Different products/teams must share the platform safely without cross-tenant leakage.

### How implemented
- `workspace_id` scopes channels, jobs, and runtime processing context.
- Workspace validation is performed before job creation.
- Worker logs and job updates carry workspace context for traceability.

### Guardrails
- Never create a delivery job without `workspace_id`.
- All new persistence indexes/queries must preserve workspace isolation where relevant.

## Provider Abstraction
### Why
Provider SDKs evolve and each provider has different APIs/error behavior.

### How implemented
- `NotificationSenderPort` defines a common `send(job, provider_account)` contract.
- `SenderRegistry` resolves concrete sender by `provider_key`.
- Outbound adapters (`TelegramNotifier`, `EmailNotifier`) hide provider-specific details.

### Guardrails
- Keep provider-specific logic out of use cases.
- New provider support should not require changing domain entities.

## Queue-Based Processing (Durable Job Table Pattern)
### Why
API latency should stay stable even when providers are slow/unavailable.

### How implemented
- API use case persists `DeliveryJob` records with `PENDING` status.
- Worker claims due jobs using DB locking and lease fields.
- Delivery execution happens asynchronously in worker process.

### Guardrails
- API must not call provider SDKs directly.
- Worker claim logic must remain atomic and lease-aware.

## Idempotency
### Why
External callers or upstream systems may retry the same event.

### How implemented
- Event fingerprint generated from deterministic event attributes + canonical payload.
- Channel fingerprint derived from `(event_fingerprint, channel_id)`.
- `idempotency_keys` claim prevents duplicate job creation per channel.

### Guardrails
- Do not remove/relax unique dedupe key constraints.
- Payload canonicalization must remain deterministic.

## Fault Tolerance
### Why
Provider/network failures are expected in distributed systems.

### How implemented
- Worker classifies transient errors (`TimeoutError`, `ConnectionError`, `OSError`).
- Exponential backoff: retry delay = `2 ** retry_count` seconds.
- Final failure transitions job to `FAILED` with bounded error text.

### Guardrails
- Preserve status transitions (`PENDING`, `PROCESSING`, `SUCCESS`, `FAILED`).
- Always release processing lease fields when finishing a job state update.
