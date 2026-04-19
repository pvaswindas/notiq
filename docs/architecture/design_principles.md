# Design Principles

## 1. Accept Fast, Deliver Asynchronously
Why:
- Provider APIs are slow, failure-prone, and outside the control of the calling product.

How:
- Intake endpoints stop at validation, routing, dedupe, and job persistence.
- External sending happens later in the worker runtime.

Constraint:
- A successful intake response means "accepted into the delivery pipeline," not "provider confirmed delivery."

## 2. Persist Enough Context To Retry Safely
Why:
- Workers must be able to retry delivery without reconstructing upstream request context or re-reading mutable provider secrets from unrelated places.

How:
- `provider_accounts.credentials` stores structured credentials as JSON.
- `delivery_jobs.event_payload` stores the event payload used for outbound delivery.

Constraint:
- New providers should store credentials in structured form, not opaque ad hoc string fields.

## 3. Deterministic Idempotency
Why:
- Upstream retries are expected and duplicate fan-out must be controlled.

How:
- Build an event fingerprint from stable event inputs.
- Build a channel-level fingerprint from the event fingerprint plus channel identity.
- Claim the dedupe key before persisting the job.

Constraint:
- Fingerprint inputs must remain stable. Seemingly small changes to canonicalization can create duplicate deliveries.

## 4. Strict Workspace Isolation
Why:
- Notiq is multi-tenant and tenant mistakes are architectural failures, not minor bugs.

How:
- Workspace checks happen in use cases and auth dependencies.
- Channels, provider accounts, and API keys are validated against the caller's workspace.

Constraint:
- Global behavior is the exception. If something is allowed outside workspace scope, it must be deliberate and documented.

## 5. Replaceable Integrations
Why:
- Provider and infrastructure choices will change over the life of the system.

How:
- Use cases depend on ports.
- Concrete implementations are chosen only in bootstrap wiring.

Constraint:
- Application code must remain valid even if Postgres, Redis, or a provider adapter is swapped out.

## 6. Explicit Failure Semantics
Why:
- Operators need predictable behavior under partial outages and misconfiguration.

How:
- Delivery work moves through a documented state machine.
- Retryable and terminal failures are classified centrally in `ProcessDeliveryJobUseCase`.
- Rate-limit deferrals are persisted as a normal scheduling outcome, not hidden in memory.

Constraint:
- Changes to retry timing, state transitions, or error capture must be reflected in both code and documentation.

## 7. Compatibility Without Architectural Regression
Why:
- Existing clients still rely on `/events` and other compatibility-era endpoints.

How:
- Compatibility adapters translate old shapes into the current use cases instead of keeping a second workflow alive.

Constraint:
- Net-new notification capabilities should land in the modular notifications layer first, then be exposed through compatibility paths only if truly needed.
