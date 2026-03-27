# Notifications Module

## Purpose

The notifications module owns the full lifecycle of notification intake and delivery orchestration for Notiq.
It converts inbound workspace events into provider-delivery jobs while enforcing reliability policies such as idempotency, rate control, retry backoff, and lifecycle tracking.

## Responsibilities

- Accept notification requests from inbound adapters
- Validate and orchestrate event-to-channel routing
- Enforce workspace-scoped rate limiting and deduplication
- Persist delivery jobs for asynchronous processing
- Execute delivery jobs through provider abstractions
- Track delivery state transitions and retry behavior

## Boundaries

This module does **not**:
- Perform framework bootstrapping (handled in `src/bootstrap/`)
- Implement concrete storage engines beyond adapter seams
- Embed external SDK concerns in domain/application logic
- Encode product-specific business rules in event payload schemas

## Internal Structure

### `domain/`
Core business definitions and policies.

Contains:
- Entities (`Event`, `Channel`, `DeliveryJob`)
- Value objects and domain services
- Repository contracts where domain policy requires persistence abstractions

### `application/`
Workflow orchestration and use cases.

Contains:
- `SendNotificationUseCase` (intake workflow)
- `ProcessDeliveryJobUseCase` (delivery execution workflow)
- DTOs, mapping logic, sender registry service

### `ports/`
Hexagonal contracts consumed by application/domain.

Contains interfaces for:
- Delivery persistence
- Provider sending
- Registry resolution
- ID generation

### `adapters/`
Protocol-specific integration points.

Contains:
- Inbound HTTP routing and schema mapping
- Outbound provider adapters (Telegram)

## Interaction Model

1. Inbound adapter creates an application command.
2. Application use case orchestrates domain rules and ports.
3. Infrastructure adapters implement those ports at runtime.
4. Worker pulls persisted jobs and invokes processing use case.
5. Outbound adapter performs provider delivery call.

This design keeps the module stable while enabling independent replacement of delivery providers and storage technologies.
