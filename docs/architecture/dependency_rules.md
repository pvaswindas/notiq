# Dependency Rules

## Allowed Dependency Direction
Primary modular path:
- `bootstrap -> application`
- `adapters(inbound/outbound) -> application or ports`
- `application -> domain + ports`
- `infrastructure -> ports (+ local infra utilities)`

Compatibility path follows the same inward rule even if package names differ.

## Layer Capability Rules
### Domain
CAN:
- Define entities, value objects, and pure policy services.
- Validate invariants and state transitions.

MUST NOT:
- Import FastAPI, Celery, SQLAlchemy, Redis clients, or provider SDKs.
- Execute I/O directly.

### Application
CAN:
- Coordinate domain behavior and call ports.
- Decide validation, routing, dedupe, and retry order.

MUST NOT:
- Instantiate concrete infrastructure adapters.
- Write SQL or call provider HTTP clients directly.

### Ports
CAN:
- Describe required behaviors and method contracts.

MUST NOT:
- Depend on infrastructure frameworks.
- Hide side effects behind ambiguous method names.

### Adapters
CAN:
- Map transport payloads to commands/entities.
- Convert infrastructure/provider errors to adapter-level outcomes.

MUST NOT:
- Hold core business branching that belongs in use cases.

### Infrastructure
CAN:
- Implement ports with transactions, locks, retries, and connection concerns.

MUST NOT:
- Introduce domain policy forks that disagree with application rules.
- Leak ORM model objects into domain/application APIs.

### Bootstrap
CAN:
- Assemble concrete dependencies and configure runtime.

MUST NOT:
- Host feature/business logic.

## PR Review Guardrails
1. Verify no inward layer imports outward technologies.
2. Verify use cases reference interfaces, not concrete adapters.
3. Verify adapters remain mapping layers, not policy engines.
4. Verify new integration behavior is documented in `docs/`.
