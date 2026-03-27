# Notiq

Notiq is a multi-tenant notification infrastructure platform for accepting product events and delivering notifications through external providers such as Telegram.

It exists to prevent every product team from rebuilding the same operationally sensitive notification pipeline: routing, deduplication, throttling, retries, and asynchronous delivery.

## 1. Introduction

In most systems, notifications begin as application events (`user.created`, `payment.failed`, etc.).
Without a dedicated platform, event handling logic is duplicated across services, delivery reliability is inconsistent, and provider integrations leak into business code.

Notiq centralizes this concern.
It provides a clean API for event submission and a backend pipeline that handles delivery orchestration with clear architectural boundaries.

## 2. Core Concepts

### Workspace
A workspace is the tenant boundary. All channels, limits, and delivery jobs are scoped to a workspace.

### Channel
A channel is a configured delivery destination for a workspace (for example, a Telegram chat).
It includes a provider key and destination address.

### Event
An event is the inbound notification trigger. It contains an event name, payload, and workspace context.
The event payload remains intentionally generic.

### DeliveryJob
A delivery job is the executable delivery unit produced from `(event, channel)`.
It tracks lifecycle status (`PENDING`, `PROCESSING`, `SUCCESS`, `FAILED`), retry state, and error context.

## 3. High-Level Architecture

Notiq uses Hexagonal Architecture (Ports and Adapters) inside a modular monolith.

Why this architecture:
- Keep business logic independent from frameworks and providers
- Make infrastructure replaceable without touching core logic
- Keep testing focused and deterministic at each boundary

High-level layers:
- `domain`: entities, value objects, policy services
- `application`: use cases and orchestration
- `ports`: contracts consumed by application/domain
- `adapters`: HTTP and provider-specific integrations
- `infrastructure`: concrete persistence/queue/idempotency implementations
- `bootstrap`: dependency injection and runtime startup/workers

## 4. Notification Flow

End-to-end runtime flow:
1. Client sends `POST /notifications/send` with workspace + event payload.
2. HTTP adapter maps request to `SendNotificationUseCase`.
3. Use case validates input, checks workspace rate limits, and computes idempotency fingerprints.
4. Active channels are selected for the workspace.
5. One `DeliveryJob` is created per channel and persisted in the delivery queue store.
6. Background worker polls pending delivery jobs in batches.
7. `ProcessDeliveryJobUseCase` executes each job.
8. Sender registry resolves provider adapter (for example Telegram).
9. Provider attempts delivery.
10. Job transitions to `SUCCESS`, `PENDING` (with backoff), or `FAILED`.

## 5. Project Structure

```text
src/
  bootstrap/
    app.py                     # FastAPI app factory and lifecycle hooks
    container.py               # Composition root (dependency injection)
    workers/
      notification_worker.py   # Polling worker for delivery jobs

  modules/
    notifications/
      domain/                  # Entities, value objects, policies
      application/             # Use cases, DTOs, mappers, registry
      ports/                   # Interface contracts
      adapters/                # HTTP inbound, provider outbound

  infrastructure/
    persistence/               # In-memory repositories
    queue/                     # Queue abstraction/adapter (legacy seam)
    id_generator/              # ID generation implementation

  shared/                      # Shared utilities
```

## 6. Running the System

### Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 src/main.py
```

### Basic runtime validation

```bash
python3 -m compileall -q src
```

### Tests

Automated tests are not yet committed in this baseline.
Use syntax validation plus API smoke checks during development:

```bash
python3 -m compileall -q src
curl -X POST http://127.0.0.1:8000/notifications/send \
  -H 'Content-Type: application/json' \
  -d '{"workspace_id":"workspace-1","event_id":"evt-1","event_name":"healthcheck","payload":{}}'
```

### Example request

```bash
curl -X POST http://127.0.0.1:8000/notifications/send \
  -H 'Content-Type: application/json' \
  -d '{
    "workspace_id": "workspace-1",
    "event_id": "evt-1001",
    "event_name": "order.created",
    "payload": {"order_id": "ORD-42", "total": 1999}
  }'
```

## 7. Future Roadmap

- Replace in-memory repositories with durable database-backed adapters
- Introduce provider-specific transient/permanent error taxonomy
- Add dead-letter handling for repeatedly failed jobs
- Add metrics, tracing, and structured logging sinks
- Add additional providers (email, Slack, webhooks)
