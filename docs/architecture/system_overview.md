# Notiq System Overview

## What The System Does
Notiq is a multi-tenant notification platform that accepts application events, turns them into durable delivery work, and sends them through provider adapters such as Telegram and Email.

At runtime the system exposes three API families:
- Notification intake: `POST /notifications/send` and the legacy compatibility endpoint `POST /events`.
- Workspace-scoped management: workspaces, provider accounts, channels, and API keys.
- Platform administration: `/admin/*` endpoints for RBAC, rate-limit configuration, and audit visibility.

## Why The System Exists
The platform exists so product services do not need to solve the same operational problems repeatedly inside feature code:
- Multi-tenant routing and isolation.
- Safe provider credential ownership.
- Idempotent event intake.
- Durable asynchronous delivery and retries.
- Delivery throttling.
- Auditability for operational changes.

Without this separation, provider SDKs, retry policy, and tenant-specific configuration would leak into product services and become hard to evolve safely.

## Architecture Style
Notiq is a modular monolith that applies hexagonal architecture around the notification pipeline.

The architectural center of gravity is `src/modules/notifications`:
- `domain` defines notification language and invariants.
- `application` coordinates intake and delivery execution.
- `ports` define required side effects.
- `adapters` translate HTTP and provider protocols.
- `infrastructure` implements persistence, Redis-backed safety checks, and ID generation.
- `bootstrap` wires concrete dependencies for API and worker runtimes.

Compatibility and admin code still lives outside the notifications module, but both surfaces route into the same persistence model and infrastructure foundations. New production delivery behavior should be added to the notifications module first.

## High-Level Runtime Topology
1. `src/main.py` starts FastAPI through `src/bootstrap/app.py`.
2. `ContainerFactory` wires repositories, provider senders, validators, and use cases.
3. Intake endpoints call `SendNotificationUseCase`, which validates workspace state, resolves channels and provider accounts, claims idempotency keys, and persists `delivery_jobs`.
4. `src/run_worker.py` starts `NotificationWorker`, which claims due jobs in batches and hands each claimed job to `ProcessDeliveryJobUseCase`.
5. `ProcessDeliveryJobUseCase` enforces delivery safety rules, sends through the correct provider adapter, and persists `SUCCESS`, retryable `PENDING`, or terminal `FAILED`.

## Public API Surface
- `POST /notifications/send`
- `POST /events`
- `POST /workspaces`
- `GET /workspaces/{workspace_id}`
- `GET /workspaces`
- `POST /provider-accounts`
- `GET /provider-accounts`
- `GET /provider-accounts/{provider_account_id}`
- `POST /channels`
- `GET /channels`
- `PATCH /channels/{channel_id}`
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
- `PATCH /admin/workspaces/{workspace_id}/disable`
- `POST /admin/rate-limit-configs`
- `PUT /admin/rate-limit-configs/{config_id}`
- `DELETE /admin/rate-limit-configs/{config_id}`
- `GET /admin/audit-logs`
- `GET /admin/audit-logs/{resource}/{resource_id}`

## Architectural Intent
- Accept requests quickly, then hand off provider work to durable asynchronous processing.
- Keep provider credentials and delivery payloads durable so workers can retry without reconstructing external context.
- Keep policy decisions in use cases and domain services, not in HTTP routes or repositories.
- Keep infrastructure replaceable behind ports.
- Preserve compatibility contracts without creating a second business workflow.
