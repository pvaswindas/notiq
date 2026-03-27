# Notiq Architecture

## Purpose

This document explains how Notiq applies Hexagonal Architecture and why that structure matters for reliability, maintainability, and evolution.

## What Hexagonal Architecture Means in Notiq

Hexagonal Architecture (Ports and Adapters) separates core business logic from external concerns.
The core logic defines *what must happen*.
Adapters and infrastructure define *how interactions happen with the outside world*.

In Notiq, this means notification policies and orchestration are isolated from FastAPI, Telegram APIs, and storage implementations.

## Layer Responsibilities

### `domain/`
Contains business concepts and policies.

Includes:
- Entities (`Event`, `Channel`, `DeliveryJob`)
- Value objects (fingerprints, provider keys)
- Domain services (idempotency hash generation, rate limiting policy)
- Domain repository contracts where policy-level persistence abstraction is needed

Rules:
- No framework dependencies
- No network/database calls
- Deterministic logic where possible

### `application/`
Contains use cases that orchestrate domain behavior and port interactions.

Includes:
- `SendNotificationUseCase` for intake orchestration
- `ProcessDeliveryJobUseCase` for execution orchestration
- DTOs, mappers, and sender registry service

Rules:
- Coordinates work across domain + ports
- Does not call concrete provider SDKs directly
- Encodes workflow, sequencing, and failure handling

### `ports/`
Contains interfaces used by application/domain.

Examples:
- Delivery job repository contract
- Notification sender contract
- Sender registry contract
- ID generator contract

Rules:
- No implementation details
- No storage/provider logic
- Defines stable boundaries for replaceable adapters

### `adapters/`
Contains external interfaces and protocol mapping.

Inbound adapters:
- HTTP routes and request/response schemas

Outbound adapters:
- Telegram sender implementation

Rules:
- No business orchestration
- Convert protocol-specific data to/from application model

### `infrastructure/`
Contains concrete technical implementations.

Examples:
- In-memory persistence repositories
- In-memory queue adapter
- UUID generator

Rules:
- Implements ports/contracts
- Can be replaced (e.g., PostgreSQL, Redis) without changing use case logic
- May include environment-specific constraints

### `bootstrap/`
Contains runtime composition and lifecycle management.

Includes:
- Container wiring
- App startup/shutdown hooks
- Worker process loops

Rules:
- Single composition root
- No business policy decisions

## Dependency Direction

Allowed dependency direction:

`adapters/infrastructure/bootstrap -> application -> domain`

And:

`application/domain -> ports (contracts)`

Not allowed:
- `domain -> infrastructure`
- `application -> concrete adapters`

This one-way dependency direction prevents inward layers from coupling to technical details.

## Why This Prevents Tight Coupling

1. Business logic remains stable while delivery technologies evolve.
2. Integration points become explicit and testable seams.
3. New providers or persistence backends can be introduced by implementing ports.
4. Runtime wiring changes happen in `bootstrap` rather than in domain/application code.
5. Reliability improvements (retries, idempotency, lifecycle state) can be introduced without redesigning external adapters.

## Practical Example

When Notiq added persisted delivery jobs and polling workers:
- `domain` evolved `DeliveryJob` state model
- `ports` introduced delivery repository abstractions
- `infrastructure` implemented in-memory repository behavior
- `application` updated orchestration for retries and transitions
- `bootstrap` rewired dependencies

No layer violated boundaries, so the change remained incremental and controlled.
