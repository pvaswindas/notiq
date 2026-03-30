# Adding a New Channel

## Goal
Add channel configurations safely so events route to intended destinations.

## How to Extend
1. Insert channel record in `channels` table with:
- `channel_id`
- `workspace_id`
- `provider_key`
- `destination`
- Optional `provider_account_id`
- `is_active`
2. Ensure referenced workspace exists and is active.
3. Ensure provider account setup supports resolution path:
- explicit account on channel, or
- workspace default, or
- system default
4. Test with `POST /notifications/send` and optional `channel_ids` targeting the new channel.

## Behavior Notes
- Inactive channels are ignored by routing.
- `channel_ids` request field only filters among active channels.
- Duplicate event/channel combinations are prevented by idempotency claims.

## Safety Rules
- Keep `channel_id` stable (do not recycle IDs).
- Prefer explicit provider account for high-security or strict isolation channels.
- Avoid deleting channels that still have related delivery job history unless data retention policy supports it.
