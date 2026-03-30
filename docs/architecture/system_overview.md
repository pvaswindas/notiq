# Notiq System Overview

## What Is Notiq
Notiq is a multi-tenant notification orchestration platform. It receives product events through an HTTP API, expands each event into channel-specific delivery jobs, and asynchronously delivers those jobs through provider adapters (for example, Telegram or Email).

## Core Purpose
Notiq exists to centralize notification reliability concerns that are otherwise duplicated in product services:
- Event-to-channel routing
- Per-channel idempotency (duplicate suppression)
- Asynchronous delivery execution
- Retry and failure lifecycle tracking
- Provider abstraction for extensibility

## High-Level Design
Notiq follows Hexagonal Architecture (Ports and Adapters) inside a modular monolith.

### Runtime components
- API process: FastAPI route receives events and enqueues delivery jobs into Postgres.
- Worker process: Polls due jobs from Postgres, resolves sender adapters, performs delivery, and updates job state.
- Database: Stores tenants, channels, provider accounts, idempotency keys, and delivery job lifecycle.

### Primary data model
- `Workspace`: Tenant boundary.
- `Channel`: Delivery routing config per workspace.
- `ProviderAccount`: Credentials reference and default/fallback account behavior.
- `DeliveryJob`: Durable execution unit with retry and status fields.

### Entry points
- API: `POST /notifications/send`
- Worker loop: `python -m src.run` with `APP_MODE=worker`

## Why this structure works
- Business rules are isolated from frameworks and SDKs.
- Infrastructure can be replaced via ports without rewriting use cases.
- Async worker model decouples API latency from provider latency/failures.
