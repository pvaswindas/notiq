# Adding New Feature

## Goal
Ship new behavior without violating layer boundaries, tenant isolation, or delivery reliability guarantees.

## Safe Extension Workflow
1. Decide whether feature belongs to primary modular flow or compatibility flow.
2. Model new domain language/invariants first (when needed).
3. Implement or adjust application use-case orchestration.
4. Add/refine ports for new side effects.
5. Implement adapters/infrastructure behind those ports.
6. Wire dependencies in bootstrap/container.
7. Update docs and docstrings in the same change.

## Architecture Rules
- Prefer `src/modules/notifications` for all net-new production behavior.
- Keep controllers/routes/task wrappers thin and translation-focused.
- Keep retry, dedupe, and routing policies in application/domain layers.

## Common Mistakes
- Putting provider-specific branching in use cases.
- Returning provider-delivered semantics from intake endpoints.
- Accessing ORM session directly from application layer.
- Skipping workspace ownership checks in compatibility APIs.

## Feature Checklist
1. Endpoints updated in `docs/api` with real payloads and errors.
2. `docs/flows` reflects success and failure continuation.
3. `docs/architecture` and dependency rules still hold.
4. Modified classes/functions contain architecture-grade docstrings.
5. Any schema changes include migration + documentation updates.
