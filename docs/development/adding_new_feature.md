# Adding New Feature

## Goal
Ship new behavior without violating layer boundaries, tenant isolation, or delivery reliability guarantees.

## Safe Extension Workflow
1. Decide whether the feature belongs to the primary modular flow or a compatibility surface.
2. Model new domain language and invariants first when needed.
3. Implement or adjust application use-case orchestration.
4. Add or refine ports for new side effects.
5. Implement adapters and infrastructure behind those ports.
6. Wire dependencies in bootstrap or composition roots.
7. Update docs and docstrings in the same change.

## Architecture Rules
- Prefer `src/modules/notifications` for all net-new production behavior.
- Keep controllers, routes, and runtime wrappers thin and translation-focused.
- Keep retry, dedupe, and routing policies in application or domain layers.
- Preserve replayable worker inputs. If workers need data later, persist it explicitly.

## Common Mistakes
- Putting provider-specific branching in use cases.
- Returning provider-delivered semantics from intake endpoints.
- Accessing ORM session directly from the application layer.
- Skipping workspace ownership checks in compatibility APIs.
- Storing provider credentials in ad hoc string fields when the provider needs structured configuration.

## Feature Checklist
1. Endpoints updated in `docs/api` with real payloads and errors.
2. `docs/flows` reflects success and failure continuation.
3. `docs/architecture` and dependency rules still hold.
4. Modified classes and functions contain architecture-grade docstrings.
5. Any schema changes include migration and documentation updates.
6. New persistence fields explain why they are needed for retries, isolation, or observability.
