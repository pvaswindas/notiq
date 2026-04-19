# Architecture Pattern

## Selected Pattern
Notiq uses hexagonal architecture within a modular monolith.

This means the system is deployed as one application, but the notification pipeline is still designed as if its core logic must survive framework, database, and provider changes.

## Why This Pattern Fits
- Notification policy changes more slowly than transport and provider integrations.
- The system has two inbound execution styles: synchronous HTTP intake and asynchronous worker execution.
- The system has several outbound concerns: Postgres persistence, Redis-backed rate limiting, and provider API calls.
- New engineers need obvious extension seams so they can add providers or management APIs without weakening delivery guarantees.

## Layer Responsibilities
### Domain (`src/modules/notifications/domain`)
What it does:
- Defines entities such as `Workspace`, `Channel`, `ProviderAccount`, and `DeliveryJob`.
- Encodes core invariants such as retry count validity and normalized notification language.
- Provides pure domain services like idempotency fingerprint generation.

Why it exists:
- This is the only layer that should describe notification concepts without caring how data is stored or transported.

### Application (`src/modules/notifications/application`)
What it does:
- Turns commands into business outcomes.
- Coordinates repository calls, provider-account resolution, message mapping, and job state transitions.
- Owns the execution order of validation, dedupe, throttling, retry, and persistence.

Why it exists:
- The application layer is where policy becomes an executable workflow, while still staying independent of concrete infrastructure.

### Ports (`src/modules/notifications/ports`)
What it does:
- Declares the contracts the application needs from the outside world.

Why it exists:
- Ports keep the business workflow stable while repository or provider implementations change.

### Adapters (`src/modules/notifications/adapters`, `src/adapters/http`)
What it does:
- Converts HTTP requests into commands and use-case inputs.
- Converts provider-specific APIs into the outbound sender contract.

Why it exists:
- Adapters isolate protocol details and compatibility concerns from the business workflow.

### Infrastructure (`src/infrastructure`)
What it does:
- Implements persistence repositories, Redis-backed rate limiting, SQLAlchemy models, and supporting runtime utilities.

Why it exists:
- This layer owns side effects and operational mechanics, but should never redefine policy that belongs to the application or domain layer.

### Bootstrap (`src/bootstrap`, runtime entrypoints)
What it does:
- Assembles the object graph for the API and worker processes.

Why it exists:
- A single composition root makes dependencies explicit and prevents controllers or use cases from self-instantiating infrastructure.

## DOs And DON'Ts
### Domain
DO:
- Add immutable entities and value objects.
- Keep validation deterministic and framework-free.

DON'T:
- Import FastAPI, SQLAlchemy, Redis, `httpx`, or provider SDKs.
- Read environment variables or open network/database connections.

### Application
DO:
- Decide workflow order.
- Call ports and pure services explicitly.
- Keep retry, routing, and throttling decisions centralized.

DON'T:
- Instantiate concrete repositories or provider senders.
- Depend on ORM models or HTTP request objects.

### Adapters
DO:
- Translate external payloads and map errors to protocol responses.
- Preserve compatibility contracts when old routes still exist.

DON'T:
- Re-implement dedupe, retry, or delivery policy.
- Reach around use cases directly into unrelated repositories unless the adapter is explicitly a compatibility boundary.

### Infrastructure
DO:
- Handle transactions, row locking, persistence mapping, and client integration details.
- Preserve durability for provider credentials and delivery payloads.

DON'T:
- Leak SQLAlchemy models across layer boundaries.
- Introduce behavior that disagrees with documented use-case sequencing.

### Bootstrap
DO:
- Own runtime wiring and environment-backed configuration.

DON'T:
- Become a second application layer.

## Compatibility Slice
Legacy and admin surfaces still exist outside `src/modules/notifications`. They are allowed to remain for contract continuity, but they should route into shared services, persistence, and policy rather than inventing separate notification logic.

## Safe Extension Rule
For new behavior, prefer this sequence:
1. Model or clarify the business concept.
2. Update the use case or add a new one.
3. Extend ports.
4. Implement infrastructure or provider adapters.
5. Wire the dependency in `ContainerFactory`.
6. Update endpoint, flow, and development docs in the same change.
