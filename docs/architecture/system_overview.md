# Notiq System Overview

## What The System Does
Notiq is a multi-tenant notification platform that accepts product events, resolves workspace-specific routing, and executes provider delivery asynchronously.

The running API exposes two ingestion families:
- Primary modular endpoint: `POST /notifications/send`.
- Compatibility endpoints: `POST /events`, workspace/channel management, and API-key management.
- Administrative RBAC endpoints under `/admin` for operator authentication and access control management.

## Why The System Exists
Notiq centralizes hard reliability and safety concerns that are expensive to duplicate across product services:
- Workspace isolation.
- Deterministic idempotency.
- Asynchronous delivery with retries.
- Provider-account resolution and sender abstraction.
- Operational traceability of delivery attempts.
- Administrative governance (admin identities, roles, and permissions) for controlled platform operations.

This allows product services to emit events while Notiq owns delivery orchestration.

## Architecture Style
The repository is a modular monolith with hexagonal boundaries, with a transitional compatibility slice still present.

Primary production orchestration is under `src/modules/notifications` with clean layers:
- `domain`: core notification language and invariants.
- `application`: use-case orchestration.
- `ports`: stable contracts.
- `adapters`: protocol translators.
- `infrastructure`: concrete implementations.
- `bootstrap`: composition roots.

Compatibility behavior exists in legacy paths (`src/application`, `src/domain`, `src/adapters`, `src/ports`) and should be extended only when backward compatibility requires it.

## High-Level Runtime Topology
1. API process starts via `src/main.py` and wires routes in `src/bootstrap/app.py`.
2. Primary notification intake persists delivery jobs in PostgreSQL.
3. Delivery jobs are processed asynchronously by worker logic (`ProcessDeliveryJobUseCase`) and sender adapters.
4. Compatibility `/events` flow enqueues Celery tasks and uses Redis-backed idempotency and throttling controls.

## Public API Surface
- `POST /notifications/send`
- `POST /events`
- `POST /workspaces`
- `GET /workspaces/{workspace_id}`
- `GET /workspaces`
- `POST /workspaces/{workspace_id}/channels`
- `GET /workspaces/{workspace_id}/channels`
- `PUT /channels/{channel_id}`
- `PATCH /channels/{channel_id}/disable`
- `POST /workspaces/{workspace_id}/api-keys`
- `GET /workspaces/{workspace_id}/api-keys`
- `PATCH /api-keys/{api_key_id}/disable`
- `POST /admin/auth/login`
- `GET /admin/me`
- `POST /admin/admins`
- `GET /admin/admins`
- `POST /admin/admins/{admin_id}/roles`
- `PATCH /admin/admins/{admin_id}/disable`
- `POST /admin/roles`
- `GET /admin/roles`
- `POST /admin/permissions`
- `GET /admin/permissions`
- `POST /admin/roles/{role_id}/permissions`
- `GET /admin/roles/{role_id}/permissions`

## Core Architectural Intent
- Keep policy decisions in use cases and domain services.
- Keep infrastructure replaceable behind ports.
- Keep API adapters thin and protocol-focused.
- Preserve compatibility endpoints without letting them become the default extension path.
- Keep RBAC authorization decisions explicit and documented for every admin endpoint.
