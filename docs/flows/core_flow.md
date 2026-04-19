# Core Flow (`POST /notifications/send`)

## Purpose
Describe the primary notification-intake flow that turns one inbound event into zero-or-more persisted delivery jobs.

## Step-By-Step Flow
1. Client sends `workspace_id`, `event_id`, `event_name`, optional `payload`, and optional `channel_ids`.
2. HTTP route validates shape via `SendNotificationRequest` and creates `SendNotificationCommand`.
3. `SendNotificationUseCase.execute` validates required identifiers.
4. Workspace is loaded and must exist and be active.
5. Active channels are loaded for the workspace.
6. If `channel_ids` is provided, the route scope is narrowed to the matching active channels only.
7. An immutable domain `Event` is constructed from request data.
8. `IdempotencyService` creates a stable event fingerprint.
9. For each selected channel:
   - `ProviderAccountResolver` validates which provider account will be used.
   - A channel-level fingerprint is derived from the event fingerprint plus `channel_id`.
   - The idempotency repository attempts an atomic claim.
   - If the claim fails, that channel path is counted as a duplicate and no job is created.
   - If the claim succeeds, `EventMessageMapper` generates the outbound message.
   - A `DeliveryJob` is created with destination, provider, provider account, message, and the full event payload.
   - The job is persisted in `PENDING`.
10. The endpoint returns `enqueued_jobs` and `skipped_duplicates`.

## Internal Decisions
### Routing
- Default fan-out target is all active channels for the workspace.
- `channel_ids` narrows but does not expand channel selection.

### Account Resolution
- Explicit invalid or missing channel accounts are treated as hard misconfiguration for that channel path.

### Duplicate Handling
- Duplicate suppression is channel-scoped.
- A duplicate on one channel does not block other channels in the same request.

## Failure Handling
- `422`: Request payload violates schema constraints.
- `500`: Route does not normalize use-case `ValueError` or `LookupError`, so validation and misconfiguration failures currently bubble as server errors.
- Duplicate claims are not errors; they are reported in `skipped_duplicates`.

## Flow Continuation
`PENDING` jobs move to asynchronous execution handled by worker processing in `docs/flows/processing_flow.md`.
