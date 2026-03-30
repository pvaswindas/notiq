# Coding Guidelines

## DOs
- Keep domain entities immutable and framework-agnostic.
- Put workflow orchestration in use cases.
- Depend on ports from application logic; inject adapters in bootstrap.
- Preserve idempotency behavior for all intake paths.
- Keep worker state transitions explicit and auditable.
- Add docstrings to all classes/functions.

## DON'Ts
- Do not import FastAPI/SQLAlchemy/provider SDKs into domain.
- Do not call provider adapters from HTTP route handlers.
- Do not bypass repository ports from use cases.
- Do not change delivery status semantics casually.
- Do not store provider secrets directly in domain models.

## Architecture Rules
1. Dependency flow must remain inward to domain.
2. New integrations should be adapter + wiring changes first.
3. Any cross-layer shortcut must be treated as architecture debt and documented.
4. Business validation errors should be normalized at API boundary (future improvement).

## Quality Rules
- Keep changes small and layered.
- Prefer deterministic mapping and hashing for idempotency-sensitive code.
- Preserve backward-compatible API contracts unless versioning is introduced.
