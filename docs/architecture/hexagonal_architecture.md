# Hexagonal Architecture in Notiq

## Layer Model
Notiq uses a strict inward dependency flow:

`inbound adapters -> application -> domain <- ports <- outbound adapters/infrastructure`

## Domain Layer (`src/modules/notifications/domain`)
### Owns
- Core entities (`Workspace`, `Channel`, `ProviderAccount`, `Event`, `DeliveryJob`)
- Value objects (`EventFingerprint`, `ProviderKey`)
- Domain policies/services (`IdempotencyService`, `RateLimitService`)

### Must do
- Express business invariants and core language
- Stay framework-agnostic

### Must not do
- No FastAPI imports
- No SQLAlchemy imports
- No provider SDK/network calls

## Application Layer (`src/modules/notifications/application`)
### Owns
- Use-case orchestration (`SendNotificationUseCase`, `ProcessDeliveryJobUseCase`)
- DTOs, mapping, routing helpers

### Must do
- Coordinate domain + ports to execute business workflows
- Enforce workflow-level validation and decision ordering

### Must not do
- No direct SQL statements
- No hardcoded framework handlers
- No provider-specific SDK logic

## Ports (`src/modules/notifications/ports`)
### Owns
- Interfaces required by application/domain to talk to external systems

### Must do
- Define behavior contracts (repositories, sender, registry, id generator)

### Must not do
- No concrete infrastructure implementation

## Adapters (`src/modules/notifications/adapters`)
### Inbound adapters
- HTTP request/response models and route handlers
- Map external protocol into commands

### Outbound adapters
- Provider-specific notification senders
- Convert generic delivery job into provider call behavior

## Infrastructure (`src/infrastructure`, `src/bootstrap`, `alembic`)
### Owns
- Postgres persistence implementations
- SQLAlchemy models/session
- Runtime composition root and worker process wiring
- Migrations and deployment runtime

### Must do
- Implement ports
- Handle concrete I/O concerns

### Must not do
- Re-implement business routing policies

## Dependency Direction Rules
1. Domain depends on nothing outside domain-level language/types.
2. Application depends on domain + ports.
3. Ports depend only on domain types (and standard library abstractions).
4. Adapters/infrastructure depend on ports/application/domain.
5. Bootstrap composes everything; no business rules in bootstrap.

## Practical Rule of Thumb
If a change requires touching only adapters/infrastructure for a new provider or storage backend, architecture is healthy.
If it forces domain rewrites for integration concerns, layering is being violated.
