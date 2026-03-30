# Dependency Rules

## Dependency Direction (Primary Notifications Module)
Allowed direction:

`adapters + infrastructure + bootstrap -> application -> domain`

`application -> ports`

`infrastructure/adapters -> ports`

## Layer DO and DON'T Rules
### Domain
DO:
- Model business entities and invariants.
- Keep logic deterministic where possible.

DON'T:
- Import FastAPI, SQLAlchemy, Celery, Redis, or provider SDKs.
- Perform network or database operations.

### Application
DO:
- Orchestrate workflows across domain and ports.
- Decide sequencing for validation, dedupe, and state transitions.

DON'T:
- Create SQL queries or call HTTP/provider SDKs directly.
- Depend on concrete infrastructure classes.

### Ports
DO:
- Declare explicit contracts and semantics.
- Use domain/application language in method signatures.

DON'T:
- Include technology-specific behavior or side effects.

### Adapters
DO:
- Translate protocol payloads to/from use-case inputs and outputs.
- Keep request/response mapping and provider I/O details localized.

DON'T:
- Implement business policy sequencing that belongs in use cases.

### Infrastructure
DO:
- Implement ports and guarantee technical concerns (transactions, locking, retries at transport layer).
- Keep persistence mapping and runtime details isolated.

DON'T:
- Re-encode domain policy decisions.
- Leak infrastructure data models into domain entities.

### Bootstrap
DO:
- Wire dependencies in one composition root.
- Keep runtime startup concerns explicit.

DON'T:
- Host business rules or feature logic.

## Legacy Path Rule
Legacy `src/application` + `src/domain` + Celery-task pipeline is compatibility code. New dependencies should not be added there unless required for backward compatibility.

## Review Checklist For PRs
1. Does any inward layer import outward technology packages?
2. Does a use case reference concrete adapter/infrastructure classes?
3. Does an adapter contain business policy branching that belongs in application?
4. Are new provider/storage additions implemented behind ports?
5. Is runtime wiring confined to bootstrap/container files?
