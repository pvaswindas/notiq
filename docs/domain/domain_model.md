# Domain Model

## Scope
The canonical production domain for notifications lives under `src/modules/notifications/domain`.

Compatibility domain objects also exist under `src/domain`, but they are maintained only for legacy route and admin behavior. New notification modeling should target the notifications module first.

## Primary Entities
### Workspace
Why it exists:
- Defines the tenant boundary and activation gate.

What problem it solves:
- Ensures all routing and execution are scoped to one tenant context.

How it interacts:
- Parent context for channels, provider-account defaults, and delivery jobs.

### Channel
Why it exists:
- Represents a delivery route configuration owned by a workspace.

What problem it solves:
- Separates destination and provider-account selection from the event itself.

How it interacts:
- Selected during fan-out.
- Supplies provider key, destination, and optional explicit provider account.
- Acts as the configuration source from which `DeliveryJob` routing fields are copied.

### ProviderAccount
Why it exists:
- Encapsulates provider credential ownership and activation status.

What problem it solves:
- Enables credential rotation, workspace scoping, and default-account fallback without mutating channels or historical jobs.

How it interacts:
- Resolved per channel by `ProviderAccountResolver`.
- Used during send execution by outbound sender adapters.
- Stores structured `credentials` JSON so different providers can evolve their credential shapes safely.

### Event
Why it exists:
- Holds immutable event identity and payload used by intake orchestration.

What problem it solves:
- Provides stable input for fingerprint computation and outbound message generation.

How it interacts:
- Combined with channels to generate channel-scoped delivery work.

### DeliveryJob
Why it exists:
- Durable executable unit for asynchronous provider delivery.

What problem it solves:
- Decouples API acceptance from provider latency and failure modes while preserving enough routing and payload context to retry later.

How it interacts:
- Created in the intake use case.
- Claimed and transitioned by the processing use case.
- Tracks retries, lease ownership, and final state.
- Carries `event_payload`, which is the source of truth for outbound delivery retries.

### ApiKey (Compatibility Auth Domain)
Why it exists:
- Models workspace-scoped machine credentials for compatibility and management APIs.

What problem it solves:
- Allows non-human services to authenticate ingestion and workspace-scoped management requests.

How it interacts:
- Auth service validates hashed key material and projects `AuthContext`.
- `/events`, channel, provider-account, and API-key routes derive workspace access control from this model.

### Admin (Administrative Domain)
Why it exists:
- Represents a human operator identity for platform governance actions.

What problem it solves:
- Enables secure login and scoped operational control separate from workspace API keys.

How it interacts:
- Authenticated by `AdminAuthService`.
- Assigned roles for permission checks on `/admin` routes.

### Role (Administrative Domain)
Why it exists:
- Groups permissions into reusable authorization bundles.

What problem it solves:
- Avoids per-admin direct permission sprawl and simplifies operational policy management.

How it interacts:
- Assigned to admins.
- Linked to permissions used by RBAC checks.

### Permission (Administrative Domain)
Why it exists:
- Defines atomic allowed admin actions such as `manage_admins` or `view_audit_logs`.

What problem it solves:
- Provides explicit, auditable authorization semantics for each privileged endpoint.

How it interacts:
- Assigned to roles.
- Evaluated by `RbacService` through admin auth dependencies.

## Relationships
- `Workspace 1 -> N Channel`
- `Workspace 1 -> N ProviderAccount`
- `Workspace 1 -> N DeliveryJob`
- `Channel 1 -> N DeliveryJob`
- `ProviderAccount 1 -> N DeliveryJob`
- `ProviderAccount 0..1 <- Channel` (optional explicit binding)
- `Workspace 1 -> N ApiKey`
- `Admin N <-> N Role`
- `Role N <-> N Permission`

## Value Objects And Domain Services
- `ProviderKey`: normalizes provider identity.
- `EventFingerprint`: typed representation of deterministic event hash.
- `IdempotencyService`: creates event and channel fingerprints.

## Modeling Guidance
- Add new notification concepts under `src/modules/notifications/domain` unless the change is explicitly compatibility-only.
- Prefer storing provider-specific shape in structured dictionaries that are validated at the application boundary, not as hard-coded columns per provider.
- Keep entity fields stable once they become persistence contracts, especially `DeliveryJob` fields that workers depend on across process boundaries.
