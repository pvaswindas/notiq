# Application Layer

## Scope
Primary orchestration for notifications is implemented in `src/modules/notifications/application`.

A compatibility orchestration path remains in `src/application/use_cases/process_event_use_case.py` for the legacy `/events` endpoint.
Administrative orchestration for RBAC/governance APIs is implemented under `src/application/admin_use_cases` and `src/application/services`.

## Primary Use Cases

### SendNotificationUseCase
What it does:
- Converts one inbound command into deduplicated persisted delivery jobs.

Decision flow:
1. Validate required command identifiers.
2. Validate workspace exists and is active.
3. Resolve active channels and apply optional `channel_ids` filter.
4. Resolve provider account per channel.
5. Compute/claim channel-level idempotency key.
6. Persist new delivery jobs for successful claims.
7. Return enqueue summary.

Important constraints:
- No direct dependency on concrete infrastructure classes.
- Per-channel dedupe behavior is intentional.

### ProcessDeliveryJobUseCase
What it does:
- Executes one claimed job and persists lifecycle transition.

Decision flow:
1. Validate provider account availability.
2. Resolve sender by provider key.
3. Attempt send.
4. Classify exception as transient/non-transient.
5. Persist `SUCCESS`, retryable `PENDING`, or terminal `FAILED`.

Important constraints:
- Lease ownership fields must be cleared on persisted outcomes.
- Retry schedule remains centralized here.

## Application Services
### ProviderAccountResolver
- Encapsulates account fallback order and validation.

### SenderRegistry
- Central lookup for provider key -> sender implementation.

### EventMessageMapper
- Produces deterministic text payloads for delivery jobs.

## Compatibility Application Behavior
Legacy `ProcessEventUseCase` fans out channels into Celery tasks.

Associated compatibility services (for example rate-limit resolution) remain valid only for `/events` behavior and should not absorb new primary architecture work.

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
6. Mint signed access token with role claims and expiration.

Important constraints:
- Token structure and expiration come from runtime settings.
- Password policy and hashing remain centralized in auth service.

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

Important constraints:
- Must reject unknown roles before creating admin.
- Must never persist plaintext passwords.

### AssignRoleUseCase
What it does:
- Assigns one role to one admin after existence checks.

Decision flow:
1. Verify admin exists.
2. Verify role exists.
3. Persist admin-role link.

Important constraints:
- Missing entities are handled as explicit `404` failures.

## Administrative Services

### AdminAuthService
- Handles admin password hashing/verification and JWT encode/decode.
- Enforces login failure semantics (`400`, `401`, `403`) used by admin auth endpoints.

### RbacService
- Resolves effective permissions for an authenticated admin.
- Used by route dependencies to guard mutating admin/role/permission endpoints.
