# Coding Guidelines

## Architecture-First Rules
- Keep domain models immutable and framework-agnostic.
- Keep use cases focused on orchestration, not I/O implementation.
- Depend on ports in application logic; instantiate concrete adapters in bootstrap.
- Preserve deterministic idempotency inputs and behavior.
- Update docs in the same change as behavior changes.

## Layer Do/Don't Summary
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

### Adapters/Infrastructure
DO:
- Handle transport, serialization, persistence, and integration I/O.

DON'T:
- Re-implement core business policies.

## Docstring Standard
- Class docstrings must cover: purpose, responsibilities, architectural role, constraints.
- Function/method docstrings must cover: behavior, args, return, internal flow, edge cases.

## Documentation Standard
- API docs are per-endpoint and must reflect actual code paths.
- Flow docs must explain routing decisions and failure behavior.
- Architecture docs must state CAN and MUST NOT rules per layer.

## Validation Expectations
- Run syntax checks (`python3 -m compileall -q src`) after code edits.
- Verify modified endpoints and auth behavior against controller code.
- Verify docs do not contradict runtime behavior.
