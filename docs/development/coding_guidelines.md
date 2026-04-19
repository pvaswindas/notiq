# Coding Guidelines

## Architecture-First Rules
- Keep domain models immutable and framework-agnostic.
- Keep use cases focused on orchestration, not I/O implementation.
- Depend on ports in application logic and instantiate concrete adapters in bootstrap.
- Preserve deterministic idempotency inputs and behavior.
- Preserve replayable worker inputs by persisting the data a retry will need.
- Update docs in the same change as behavior changes.

## Layer Do And Don't Summary
### Domain
DO:
- Encode domain language and invariants.

DON'T:
- Import framework or infrastructure dependencies.

### Application
DO:
- Coordinate decision order and lifecycle transitions.

DON'T:
- Perform SQL, HTTP handler logic, or SDK client calls.

### Adapters And Infrastructure
DO:
- Handle transport, serialization, persistence, and integration I/O.
- Keep provider credential formats explicit and validated.

DON'T:
- Re-implement core business policies.
- Return ORM models or SDK-native payloads past architectural boundaries.

## Docstring Standard
- Class docstrings must cover: purpose, responsibilities, architectural role, and constraints.
- Function and method docstrings must cover: behavior, args, return value, internal flow, and edge cases when relevant.

## Documentation Standard
- API docs are per-endpoint and must reflect actual code paths.
- Flow docs must explain routing decisions and failure behavior.
- Architecture docs must state CAN and MUST NOT rules per layer.

## Validation Expectations
- Run syntax checks with `python3 -m compileall -q src` after code edits.
- Verify modified endpoints and auth behavior against controller code.
- Verify docs do not contradict runtime behavior.
- Remove stale endpoint docs when the route no longer exists.
