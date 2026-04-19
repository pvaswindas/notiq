# Dependency Rules

## Allowed Dependency Direction
Primary modular path:
- `bootstrap -> application`
- `adapters(inbound/outbound) -> application or ports`
- `application -> domain + ports`
- `domain -> nothing outward`
- `infrastructure -> ports (+ local infra utilities)`

Compatibility path follows the same inward rule even if package names differ.

## Layer Capability Rules
### Domain
CAN:
- Define entities, value objects, and pure policy services.
- Validate invariants and state transitions.

MUST NOT:
- Import FastAPI, SQLAlchemy, Redis clients, or provider SDKs.
- Execute I/O directly.
- Read runtime configuration.

### Application
CAN:
- Coordinate domain behavior and call ports.
- Decide validation, routing, dedupe, retry, and rate-limit order.

MUST NOT:
- Instantiate concrete infrastructure adapters.
- Write SQL or call provider HTTP clients directly.
- Accept transport-layer objects such as FastAPI requests or ORM sessions as primary inputs.

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
- Preserve compatibility request/response contracts.

MUST NOT:
- Hold core business branching that belongs in use cases.
- Persist business state transitions directly when a documented use case already owns that workflow.

### Infrastructure
CAN:
- Implement ports with transactions, locks, retries, and connection concerns.
- Persist structured JSON for provider credentials and delivery payloads.

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
3. Verify compatibility routes still translate into shared workflows instead of growing side paths.
4. Verify adapters remain mapping layers, not policy engines.
5. Verify new integration behavior is documented in `docs/`.
