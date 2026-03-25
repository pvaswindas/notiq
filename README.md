# Notiq

Notiq is a **multi-tenant notification infrastructure platform** designed to handle event-driven communication across multiple delivery channels.

It provides a **scalable, extensible, and decoupled system** for routing and delivering notifications without embedding notification logic inside individual applications.

---

## Why Notiq?

Modern systems require:

* Reliable event delivery
* Multi-channel notifications (Telegram, Email, Slack, etc.)
* Decoupled infrastructure
* Asynchronous processing

Most applications re-implement this logic repeatedly.

**Notiq solves this by acting as a centralized notification engine.**

---

## Core Capabilities

* Event-driven notification processing
* Multi-tenant (workspace-based isolation)
* Channel-based routing
* Provider abstraction (Telegram today, extensible tomorrow)
* Queue-based asynchronous delivery
* Idempotent processing
* Rate limiting (extensible)
* Clean architecture (Hexagonal)

---

## Architecture Overview

Notiq follows a **Hexagonal Architecture (Ports & Adapters)** combined with a **modular monolith design**.

### Key Principles

* Business logic is isolated from infrastructure
* External systems are replaceable
* Clear separation of concerns
* Deterministic and testable core

---

## Project Structure

```
src/

  bootstrap/                # Application entry & wiring
    container.py            # Dependency injection
    workers/                # Background workers

  modules/
    notifications/
      domain/               # Core business entities & logic
      application/          # Use cases & orchestration
      ports/                # Interfaces (contracts)
      adapters/             # External interaction (HTTP, providers)

  infrastructure/           # Concrete implementations
    persistence/            # Repositories
    queue/                  # Event queue
    id_generator/           # ID generation

  shared/                   # Pure utilities (no business logic)
```

---

## Core Flow

```
HTTP Request
   ↓
SendNotificationUseCase
   ↓
EventQueue (async)
   ↓
Worker
   ↓
ProcessDeliveryJobUseCase
   ↓
SenderRegistry
   ↓
Provider (e.g., Telegram)
```

---

## Key Concepts

### Workspace

Represents a tenant. All operations are scoped to a workspace.

### Channel

Defines a delivery destination (e.g., Telegram chat).

### Provider

Handles message delivery (Telegram, Email, etc.).

### Event

A generic payload representing a notification trigger.

### Delivery Job

A queued unit of work for sending a notification.

---

## Technology Choices

* Python 3.11+
* Async-first design (`async/await`)
* In-memory implementations (initial phase)
* Designed for future:

  * Redis (queue)
  * PostgreSQL (persistence)
  * External providers

---

## Design Decisions

### Why Hexagonal Architecture?

* Decouples business logic from infrastructure
* Enables independent testing
* Makes providers replaceable

### Why Queue-Based Processing?

* Improves reliability
* Handles spikes
* Enables retries and backoff

### Why Modular Monolith?

* Simpler than microservices
* Maintains strong boundaries
* Easier to evolve

---

## Current Status

* Core architecture implemented
* Notification flow established
* In-memory infrastructure in place

> System is in **foundational stage**, ready for:
>
> * persistence upgrade
> * real queue integration
> * additional providers

---

## Running the Project

```bash
# Install dependencies (if any)
pip install -r requirements.txt

# Run application
python src/main.py
```

---

## Development Guidelines

### Strict Rules

* Do NOT mix layers
* Do NOT import infrastructure into application/domain
* Do NOT add business logic into adapters
* Keep events generic and product-agnostic

---

## Future Roadmap

* Redis-backed queue
* PostgreSQL persistence
* Slack / Email providers
* Webhook support
* Retry & dead-letter queues
* Observability (logging + tracing)
* Rate limiting enforcement
* Multi-workspace scaling

---

## Contributing

1. Follow architecture rules strictly
2. Maintain clean separation of concerns
3. Write clear docstrings
4. Avoid shortcuts that break boundaries

---

## License

This project is licensed under the terms specified in the LICENSE file.