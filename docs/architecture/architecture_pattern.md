# Architecture Pattern

## Selected Pattern
Notiq uses Hexagonal Architecture (Ports and Adapters) within a modular monolith.

## Why This Pattern Fits Notiq
- Notification policies (dedupe, retry semantics, account resolution) must stay stable while provider APIs and storage technologies evolve.
- Inbound protocols (HTTP) and outbound protocols (provider SDKs, databases, brokers) change more frequently than business workflows.
- Clear dependency seams enable targeted testing and safe extension.

## Layer Responsibilities
### Domain (`src/modules/notifications/domain`)
- Owns entities, value objects, and policy services.
- Defines invariants for notification lifecycle language.

### Application (`src/modules/notifications/application`)
- Owns business orchestration use cases.
- Enforces decision order across repositories, idempotency, and sender routing.

### Ports (`src/modules/notifications/ports`)
- Defines contracts used by application/domain.
- Shields core logic from infrastructure details.

### Adapters (`src/modules/notifications/adapters`)
- Inbound adapters translate external requests to use-case commands.
- Outbound adapters translate domain jobs to provider calls.

### Infrastructure + Bootstrap (`src/infrastructure`, `src/bootstrap`, `alembic`)
- Implements ports using concrete tech (Postgres, Redis, Celery, SQLAlchemy).
- Composes runtime object graph in one place.

## Transitional Reality
The repository also contains a legacy event-ingestion path (`src/application`, `src/domain`, `src/adapters/tasks`) used by `POST /events` and Celery fan-out. This path should be treated as compatibility infrastructure while new architecture work targets `src/modules/notifications`.

Legacy compatibility now includes a small throttling slice:
- Domain model: `src/domain/rate_limit/entities.py` (`RateLimitConfig`)
- Application service: `src/application/services/rate_limit_resolver.py`
- Ports: `src/ports/rate_limit_config_repository.py`, `src/ports/rate_limiter.py`
- Infrastructure adapters: in-memory config source and Redis limiter

This slice follows the same ports-and-adapters dependency direction as the primary module.

## Safe Extension Rule
Any new capability should first be modeled as:
1. Domain/application behavior in `src/modules/notifications`.
2. Port contract updates.
3. Adapter/infrastructure implementation.
4. Composition root wiring.

If implementation requires placing provider or persistence details directly in use cases, the design is violating the intended pattern.
