# Architecture Pattern

## Selected Pattern
Notiq uses Hexagonal Architecture inside a modular monolith.

## Why This Pattern Fits
- Notification delivery policies must stay stable while providers, queues, and persistence choices evolve.
- The system has multiple inbound protocols (HTTP and worker polling) and outbound integrations (provider APIs, Postgres, Redis).
- Strong boundaries reduce accidental coupling and make extension safer.

## Primary Module Structure
### Domain (`src/modules/notifications/domain`)
Purpose:
- Define immutable entities, value objects, and policy services.

MUST:
- Express business language and invariants.

MUST NOT:
- Know anything about HTTP, SQLAlchemy, Redis, or SDK clients.

### Application (`src/modules/notifications/application`)
Purpose:
- Orchestrate use-case decisions and lifecycle transitions.

MUST:
- Coordinate domain objects and ports in explicit sequence.

MUST NOT:
- Import concrete repositories/senders.
- Contain transport or persistence implementation details.

### Ports (`src/modules/notifications/ports`)
Purpose:
- Define integration contracts and behavioral expectations.

MUST:
- Remain technology-agnostic.

MUST NOT:
- Embed framework-specific assumptions.

### Adapters (`src/modules/notifications/adapters`)
Purpose:
- Translate between external protocols and application contracts.

MUST:
- Handle schema mapping, protocol validation, and serialization.

MUST NOT:
- Recreate business policy sequencing.

### Infrastructure + Bootstrap (`src/infrastructure`, `src/bootstrap`)
Purpose:
- Implement ports and compose runtime object graphs.

MUST:
- Keep wiring in composition roots.

MUST NOT:
- Push infrastructure concerns back into domain/application layers.

## Transitional Compatibility Slice
Legacy endpoints and tasks still exist for backward compatibility.

Guideline:
- Prefer all new behavior in `src/modules/notifications`.
- Touch legacy layers only when compatibility contracts require it.

## Extension Decision Rule
Use this order for new capabilities:
1. Model behavior in domain/application.
2. Add or refine port contracts.
3. Implement adapters/infrastructure.
4. Wire in bootstrap.
5. Update docs and docstrings in the same change.
