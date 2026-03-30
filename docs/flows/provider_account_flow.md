# Provider Account Flow

## Scope
Provider account resolution is part of the primary intake path and is executed by `ProviderAccountResolver.resolve_for_channel`.

## Resolution Order
1. Explicit channel account (`channel.provider_account_id`).
2. Workspace default account for `provider_key`.
3. System default account (`workspace_id = NULL`) for `provider_key`.

## Important Behavior
- If explicit channel account is configured but inactive/missing, resolution fails immediately.
- Defaults are only considered when explicit account is not configured.
- Inactive accounts are never selected.

## Why This Rule Exists
Fail-fast behavior on explicit account misconfiguration prevents accidental credential drift and unexpected fallback routing.

## Related Docs
- [core_flow.md](/home/aswin/code/unifiedbits/notiq/docs/flows/core_flow.md)
- [integration_flow.md](/home/aswin/code/unifiedbits/notiq/docs/flows/integration_flow.md)
