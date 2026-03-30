# Notification Flow

## End-to-End Sequence
`Event -> API -> UseCase -> DB -> Worker -> Provider -> Delivery`

## Step-by-Step
1. Client calls `POST /notifications/send` with `workspace_id`, `event_id`, `event_name`, `payload`, and optional `channel_ids`.
2. HTTP adapter (`NotificationRouterFactory`) maps request JSON to `SendNotificationCommand`.
3. `SendNotificationUseCase` validates required fields and checks workspace exists + is active.
4. Use case loads all active channels for the workspace.
5. If `channel_ids` is present, channels are filtered to only those IDs.
6. Use case computes deterministic event fingerprint from workspace/event/payload.
7. For each channel:
- Resolve provider account:
  - Explicit `channel.provider_account_id` if present and active.
  - Else workspace default for provider.
  - Else system default for provider.
- Derive channel-level dedupe key from `(event_fingerprint + channel_id)`.
- Attempt atomic idempotency key claim.
- If already claimed, increment `skipped_duplicates` and continue.
- Map event/channel into a message string.
- Create `DeliveryJob` with `PENDING` status.
- Persist job in Postgres.
8. API returns enqueue summary: `enqueued_jobs`, `skipped_duplicates`.
9. Worker loop claims due jobs in batches using lease (`processing_owner`, `processing_expires_at`).
10. `ProcessDeliveryJobUseCase` resolves sender adapter by `provider_key` and invokes provider send.
11. Job is updated to:
- `SUCCESS` on successful provider call.
- `PENDING` with retry metadata on transient errors.
- `FAILED` on non-transient errors or retry exhaustion.

## Internal Decisions Explained
### Channel selection
- Default behavior: all active channels in workspace.
- Scoped behavior: if `channel_ids` provided, only matching active channels are considered.

### Provider account resolution
- Priority is explicit channel account first.
- Then workspace-level provider default.
- Then system-level provider default (`workspace_id = null`).
- If no active account exists, flow fails for that channel/job creation path.

### Delivery durability boundary
- API success means jobs were persisted, not necessarily delivered.
- Delivery outcome is eventually consistent and managed by worker lifecycle.
