# Coding Guidelines

## Core Rules
- Keep domain entities immutable and framework-agnostic.
- Keep application use cases focused on orchestration and decision order.
- Depend on ports in use cases; instantiate adapters only in bootstrap.
- Keep idempotency behavior deterministic and explicit.
- Document every architectural behavior change in `docs/` in the same PR.

## Layer DO and DON'T
### Domain
DO:
- Encode invariants and domain language.

DON'T:
- Import framework, ORM, or SDK packages.

### Application
DO:
- Coordinate domain + ports.

DON'T:
- Implement SQL, HTTP handlers, or provider SDK calls.

### Adapters/Infrastructure
DO:
- Implement protocol and I/O details.

DON'T:
- Recreate business policy branching from use cases.

## Documentation Expectations
- Class docstrings must include purpose, responsibilities, architectural role, and key constraints.
- Function/method docstrings must include behavior, parameters, return value, flow notes, and edge cases.
- API docs must match real request/response behavior.
- Flow docs must explain success and failure branches.

## Testing and Validation Expectations
- Validate syntax (`python3 -m compileall -q src`).
- Validate migrations and schema alignment when persistence changes.
- Validate endpoint behavior with smoke calls for both ingestion endpoints.

## Compatibility Guidance
Legacy `src/application` / `src/domain` flow is maintained for compatibility. New primary features should be built in `src/modules/notifications` unless compatibility constraints require otherwise.
