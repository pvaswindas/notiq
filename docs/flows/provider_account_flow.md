# Provider Account Resolution Flow

## Purpose
Provider account resolution determines which credentials are used for each channel delivery job.

## Resolution Order
For each channel, `ProviderAccountResolver.resolve_for_channel` executes:
1. Channel-specific account
- If `channel.provider_account_id` is set, fetch that exact account.
- If missing or inactive, raise error.
2. Workspace default account
- Query default account for `(provider_key, workspace_id)`.
- Use it only when active.
3. System default account
- Query default account for `(provider_key, workspace_id=None)`.
- Use it only when active.
4. Fail when no active account found
- Raises `ValueError` and prevents job creation/processing for that path.

## Default vs Custom Logic
### Custom (explicit channel account)
- Strongest priority.
- Gives fine-grained credential control per channel.

### Default (workspace)
- Shared default account within one workspace/provider.
- Useful for teams managing many channels under same credentials.

### Default (system/global)
- Last-resort fallback for provider-wide defaults.
- Useful for bootstrap or shared platform account behavior.

## Failure and Fallback Behavior
- No fallback from explicit account to defaults when explicit ID is invalid/inactive. This is intentional to surface configuration mistakes early.
- Fallback is only used when channel does not specify an explicit account.
- Inactive accounts are treated as unavailable.

## Operational Guidance
- Use explicit account when channel-level credential isolation is required.
- Use workspace default for standard tenant setup.
- Reserve system defaults for controlled platform-wide fallback use.
