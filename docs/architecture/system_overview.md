# Notiq System Overview

## What The System Does
Notiq is a multi-tenant notification platform that converts product events into provider-specific delivery attempts.

The runtime currently exposes two ingestion paths:
- `POST /notifications/send`: primary modular flow that persists delivery jobs in PostgreSQL and processes them through a worker lease model.
- `POST /events`: legacy event-ingestion path that fans out active channels and enqueues Celery tasks.

## Why The System Exists
Notiq exists to centralize reliability concerns that are hard to implement correctly in every product service:
- Tenant-safe routing
- Duplicate suppression (idempotency)
- Asynchronous delivery and retries
- Provider abstraction and credential resolution
- Durable lifecycle tracking for delivery attempts

Without this platform, every product service would duplicate integration logic and operational failure handling.

## Architecture Style
The codebase is a modular monolith using Hexagonal Architecture (Ports and Adapters), with a transitional legacy ingestion path still present.

Primary module (`src/modules/notifications`) follows strict layering:
- `domain`: business entities, value objects, domain services
- `application`: use-case orchestration
- `ports`: interfaces for infrastructure and adapters
- `adapters`: HTTP inbound and provider outbound translators
- `infrastructure`: concrete persistence, queue, and runtime plumbing
- `bootstrap`: composition root and runtime wiring

## Core Runtime Components
- API app factory: [src/bootstrap/app.py](/home/aswin/code/unifiedbits/notiq/src/bootstrap/app.py)
- Primary composition root: [src/bootstrap/container.py](/home/aswin/code/unifiedbits/notiq/src/bootstrap/container.py)
- Primary worker orchestration: [src/bootstrap/workers/notification_worker.py](/home/aswin/code/unifiedbits/notiq/src/bootstrap/workers/notification_worker.py)
- Legacy event-ingestion composition root: [src/bootstrap/event_ingestion_container.py](/home/aswin/code/unifiedbits/notiq/src/bootstrap/event_ingestion_container.py)
- Celery app: [src/infrastructure/celery_app.py](/home/aswin/code/unifiedbits/notiq/src/infrastructure/celery_app.py)

## Bounded Contexts In Practice
### Notification Job Lifecycle (Primary)
- Ingest command and validate workspace.
- Resolve channels and provider accounts.
- Claim idempotency key per `(event, channel)`.
- Persist `delivery_jobs` rows.
- Worker claims due jobs with lease semantics.
- Delivery use case marks `SUCCESS`, schedules retry, or marks `FAILED`.

### Event Fan-Out (Legacy)
- Accept raw event (`workspace_id`, `event_type`, payload).
- Load active channels from in-memory channel repository.
- Enqueue one Celery task per `(event, channel)`.
- Task performs redis-backed idempotency claim, scoped rate-limit check, and provider send.
- Throttled attempts release idempotency key and self-requeue for a later retry.

## Architectural Intent
The primary path is engineered for durable, auditable, and replaceable delivery orchestration. The legacy path remains for compatibility and should be treated as a transitional seam, not the target for new feature investment.
