# Adding New Feature

## Goal
Add feature behavior without breaking architecture boundaries or runtime reliability.

## Safe Extension Workflow
1. Clarify whether feature belongs to primary notifications module or legacy compatibility path.
2. Model domain changes first (`src/modules/notifications/domain`) when business language changes.
3. Add/adjust application orchestration in use cases (`src/modules/notifications/application`).
4. Introduce or update port contracts if new external interaction is required.
5. Implement infrastructure/adapters behind ports.
6. Wire dependencies in composition root (`src/bootstrap/container.py`).
7. Update docs in `docs/architecture`, `docs/flows`, `docs/api`, and relevant development guides.

## Architecture Rules To Follow
- New production feature work should target modular notifications layers, not legacy `src/application` and `src/domain` paths.
- Keep business rules out of HTTP routes, Celery tasks, and repository implementations.
- Preserve deterministic idempotency behavior when introducing new routing dimensions.

## Common Mistakes To Avoid
- Adding provider-specific branching directly inside use cases.
- Returning delivery success semantics from API intake endpoint.
- Bypassing repository ports with direct ORM/session usage from application layer.
- Introducing cross-tenant queries without explicit workspace scoping.
- Adding legacy throttling logic directly inside Celery task body instead of through resolver + ports.

## Legacy Compatibility Feature Rule
When feature work must touch `/events` compatibility flow:
1. Keep policy selection in legacy application service (`RateLimitResolver`).
2. Keep backend-specific counting logic in infrastructure adapter (`RateLimiterPort` implementation).
3. Preserve idempotency-key release before any manual requeue/retry path.
4. Update `docs/api/ingest_event.md` and `docs/flows/integration_flow.md` in the same change.

## Feature Readiness Checklist
1. Do API docs reflect request/response behavior and error cases?
2. Are new or changed flow steps documented end-to-end?
3. Are failure/retry semantics explicitly covered?
4. Are docstrings updated for all modified classes/functions?
5. Is migration impact documented when schema changes are introduced?
