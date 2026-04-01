# Core Flow (`POST /notifications/send`)

## Purpose
Describe the primary notification-intake flow that turns one inbound event into zero-or-more persisted delivery jobs.

## Step-By-Step Flow
1. Client sends `workspace_id`, `event_id`, `event_name`, optional `payload`, and optional `channel_ids`.
2. HTTP route validates shape via `SendNotificationRequest` and creates `SendNotificationCommand`.
3. `SendNotificationUseCase.execute` validates required identifiers.
4. Workspace is loaded and must exist + be active.
5. Active channels are loaded for the workspace.
6. If `channel_ids` is provided, channels are filtered to that subset.
7. Event fingerprint is created from event identity.
8. For each selected channel:
   - Resolve provider account (explicit channel account first, then defaults).
   - Build channel-level dedupe fingerprint.
   - Attempt atomic idempotency claim.
   - If claim succeeds, map message and persist `DeliveryJob` in `PENDING`.
   - If claim fails, increment duplicate counter and skip.
9. API returns summary: `enqueued_jobs` and `skipped_duplicates`.

## Internal Decisions
### Routing
- Default fan-out target is all active channels for the workspace.
- `channel_ids` narrows but does not expand channel selection.

### Account Resolution
- Explicit invalid/missing channel account is treated as a hard misconfiguration for that channel path.

### Duplicate Handling
- Duplicate suppression is channel-scoped.
- A duplicate on one channel does not block other channels in the same request.

## Failure Handling
- `422`: Request payload violates schema constraints.
- `500`: Uncaught use-case failures (for example workspace/account errors) currently bubble from route layer.
- Duplicate claims are not errors; they are reported in `skipped_duplicates`.

## Flow Continuation
`PENDING` jobs move to asynchronous execution handled by worker processing (`docs/flows/processing_flow.md`).
