# Domain Model

## Workspace
### Why it exists
Defines tenant boundary for isolation, lifecycle checks, and routing context.

### Key relationships
- One workspace has many channels.
- One workspace has many delivery jobs.
- Workspace can own workspace-scoped provider default accounts.

## Channel
### Why it exists
Represents a delivery route for a workspace: provider + destination (+ optional explicit account).

### Key relationships
- Belongs to one workspace.
- May reference one provider account directly.
- Produces delivery jobs when events are submitted.

### Important behavior
- Only active channels are eligible for routing.

## ProviderAccount
### Why it exists
Represents provider credentials as a reference (`credentials_ref`) and default behavior scope.

### Key relationships
- May belong to workspace or be global (`workspace_id=None`).
- Can be explicit channel account or default fallback account.

### Default semantics
- Workspace default has priority over global default.
- Account must be active to be selected.

## DeliveryJob
### Why it exists
Durable executable unit for async delivery and retries.

### Key relationships
- Belongs to workspace and channel.
- Uses resolved provider account for provider call.
- References dedupe key for idempotent channel-level processing.

### Lifecycle
- `PENDING`: waiting to be processed.
- `PROCESSING`: currently claimed by worker lease.
- `SUCCESS`: delivered successfully.
- `FAILED`: terminal failure.

## Supporting Domain Types
- `Event`: inbound event abstraction.
- `EventFingerprint`: typed dedupe value wrapper.
- `IdempotencyService`: deterministic fingerprint generation.
