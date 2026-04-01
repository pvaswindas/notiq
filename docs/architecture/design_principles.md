# Design Principles

## 1. Accept Fast, Deliver Asynchronously
WHY:
- Provider calls are unreliable and high-latency.

HOW:
- Intake endpoints acknowledge acceptance after orchestration/persistence steps, not after provider delivery.

CONSTRAINT:
- Client-facing success means queued/accepted, not guaranteed external delivery.

## 2. Deterministic Idempotency
WHY:
- Upstream retries are normal; duplicates must be controlled.

HOW:
- Fingerprint event context and channel scope.
- Claim dedupe keys atomically before creating delivery work.

CONSTRAINT:
- Fingerprint inputs and canonicalization must remain stable across deployments.

## 3. Strict Workspace Isolation
WHY:
- Notiq is multi-tenant and must prevent cross-tenant leakage.

HOW:
- Workspace-scoped repository access and auth context checks.
- Workspace ownership checks on API-key and channel operations.

CONSTRAINT:
- New features default to workspace-scoped behavior unless explicitly global and justified.

## 4. Replaceable Integrations
WHY:
- Provider and persistence technology choices evolve.

HOW:
- Use-case logic targets ports.
- Adapter implementation choice stays in bootstrap/container wiring.

CONSTRAINT:
- Changing an integration should not require domain model rewrites.

## 5. Explicit Failure Semantics
WHY:
- Operators need predictable runtime behavior under errors.

HOW:
- Delivery state machine (`PENDING`, `PROCESSING`, `SUCCESS`, `FAILED`).
- Retry classification for transient failures.
- Structured error capture for terminal failures.

CONSTRAINT:
- Any retry/status change requires docs + migration/operational impact review.

## 6. Compatibility Without Architectural Regression
WHY:
- Existing clients still depend on legacy endpoints.

HOW:
- Keep compatibility behavior isolated and documented.
- Avoid growing legacy paths for net-new architecture work.

CONSTRAINT:
- Compatibility changes must preserve current contract and idempotency safety.
