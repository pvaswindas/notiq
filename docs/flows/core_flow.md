# Core Flow

## Scope
This document describes the primary production flow for `POST /notifications/send` in the modular notifications architecture.

## Step-By-Step
1. Client sends request to `POST /notifications/send` with workspace, event identity, payload, and optional `channel_ids`.
2. HTTP adapter validates payload via Pydantic schema and builds `SendNotificationCommand`.
3. `SendNotificationUseCase` validates required fields (`workspace_id`, `event_id`, `event_name`).
4. Use case loads workspace and rejects missing/inactive workspaces.
5. Use case builds domain `Event` object.
6. Use case loads active channels for the workspace.
7. If `channel_ids` is supplied, channels are filtered to that subset.
8. Use case computes event fingerprint.
9. For each selected channel, use case resolves provider account in order:
   - Explicit `channel.provider_account_id`
   - Workspace default account for provider
   - System default account for provider
10. Use case computes channel-level dedupe key and attempts atomic claim.
11. If dedupe claim fails, channel is counted as duplicate and skipped.
12. If claim succeeds, event+channel are mapped into outbound message text.
13. Use case creates `DeliveryJob` with initial `PENDING` status.
14. Job is persisted to `delivery_jobs` table.
15. API responds with enqueue summary (`enqueued_jobs`, `skipped_duplicates`).

## Internal Decisions
### Routing Decision
Routing defaults to all active channels unless `channel_ids` narrows the fan-out.

### Account Selection Decision
Account resolution intentionally fails fast when explicit channel account is missing/inactive; it does not silently fall back in that case.

### Idempotency Decision
Idempotency is channel-scoped, not request-scoped. One duplicate channel does not block other channels from being enqueued.

## Failure Handling
- Request schema errors return `422` from FastAPI.
- Domain/use-case errors are not yet mapped to structured `4xx`; they currently bubble as `500`.
- Idempotency collisions are treated as expected duplicates, not failures.

## Continuation
Persisted `PENDING` jobs are processed asynchronously by worker claim-and-execute flow documented in `processing_flow.md`.
