# Application Layer

## Scope
Primary orchestration for notifications is implemented in `src/modules/notifications/application`.

The legacy `/events` endpoint is only an inbound compatibility adapter over `SendNotificationUseCase`. Administrative orchestration for RBAC, rate limits, and governance APIs is implemented under `src/application/admin_use_cases` and `src/application/services`.

## Primary Use Cases
### SendNotificationUseCase
What it does:
- Converts one inbound command into deduplicated persisted delivery jobs.

Decision flow:
1. Validate required command identifiers.
2. Validate workspace exists and is active.
3. Resolve active channels and apply optional `channel_ids` filter.
4. Resolve provider account per channel.
5. Compute and claim a channel-level idempotency key.
6. Map an outbound message and persist a delivery job containing both message text and raw event payload.
7. Return enqueue summary.

Important constraints:
- No direct dependency on concrete infrastructure classes.
- Per-channel dedupe behavior is intentional.
- The use case does not attempt delivery itself.

### ProcessDeliveryJobUseCase
What it does:
- Executes one claimed job and persists the lifecycle transition.

Decision flow:
1. Validate provider account availability.
2. Validate provider-account workspace and provider match.
3. Check delivery safety and rate-limit policy.
4. Resolve sender by provider key.
5. Attempt send using the persisted event payload.
6. Classify the result as success, deferred, retryable failure, or terminal failure.
7. Persist the resulting job state.

Important constraints:
- Lease ownership fields must be cleared on persisted outcomes.
- Retry schedule remains centralized here.
- This use case is the only place that should decide retry timing for provider execution.

## Application Services
### ProviderAccountResolver
- Encapsulates account fallback order and validation.
- Allows channels to point to a specific account while still supporting workspace defaults.

### SenderRegistry
- Central lookup for `provider_key -> sender implementation`.

### EventMessageMapper
- Produces deterministic text payloads for delivery jobs.

### DeliverySafetyService
- Applies rate-limit checks before a provider call is made.
- Separates delivery throttling concerns from sender adapters so providers stay focused on transport.

## Compatibility Application Behavior
Compatibility routing is limited to translating `/events` payloads into `SendNotificationCommand`.
All enqueue and execution behavior now flows through the same modular notification use cases and worker.

## Administrative Use Cases
### LoginAdminUseCase
What it does:
- Delegates admin credential verification and JWT issuance to `AdminAuthService`.

Decision flow:
1. Normalize email and validate non-empty credentials.
2. Load admin by email.
3. Verify password hash.
4. Verify admin is active.
5. Resolve assigned roles.
6. Mint a signed access token with role claims and expiration.

### CreateAdminUseCase
What it does:
- Creates a new admin identity with optional initial role assignments.

Decision flow:
1. Normalize and validate input fields.
2. Check duplicate email.
3. Validate each requested role id exists.
4. Hash password.
5. Persist admin record.
6. Persist admin-role assignments.

### AssignRoleUseCase
What it does:
- Assigns one role to one admin after existence checks.

Decision flow:
1. Verify admin exists.
2. Verify role exists.
3. Persist the admin-role link.

## Administrative Services
### AdminAuthService
- Handles admin password hashing, verification, and JWT encode/decode.
- Enforces login failure semantics used by admin auth endpoints.

### RbacService
- Resolves effective permissions for an authenticated admin.
- Used by route dependencies to guard mutating or sensitive admin endpoints.

## Extension Guidance
- If a new feature changes delivery sequencing, start in the use case and then update supporting services and ports.
- If a provider requires a new credential shape, extend validation and sender expectations without pushing provider-specific branches into unrelated use cases.
- If a route only changes request shape, prefer adapter-only changes and keep application contracts stable.
