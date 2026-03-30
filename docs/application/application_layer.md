# Application Layer

## Use Cases

### SendNotificationUseCase
Purpose: convert inbound event command into persisted delivery jobs.

Flow responsibilities:
1. Validate required identifiers.
2. Validate workspace existence/active state.
3. Build `Event` entity.
4. Load active channels and optionally filter by `channel_ids`.
5. Resolve provider account per channel.
6. Generate channel dedupe key and claim idempotency.
7. Build `DeliveryJob` and persist.
8. Return enqueue summary DTO.

### ProcessDeliveryJobUseCase
Purpose: execute one claimed job and persist resulting lifecycle state.

Flow responsibilities:
1. Validate provider account availability.
2. Resolve sender via registry.
3. Execute sender.
4. Update status to `SUCCESS` on success.
5. On failure: retry with backoff when transient and budget remains.
6. Otherwise mark `FAILED`.

## Processor Logic
- Batch claim and execution is handled by `NotificationWorker`.
- Worker does orchestration loop only; business transition policy remains in use case.

## Routing Decisions
- Channel routing: all active channels unless `channel_ids` restricts.
- Provider routing: sender resolved by `provider_key`.
- Account routing: explicit channel account -> workspace default -> global default.

## Why application layer is critical
It is the boundary where business workflows remain stable while adapters and infrastructure evolve independently.
