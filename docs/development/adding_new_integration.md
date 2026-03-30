# Adding New Integration

## Scope
Use this guide for new outbound provider integrations, storage integrations, or queue/broker integrations.

## Pattern For New Provider
1. Implement `NotificationSenderPort` in `src/modules/notifications/adapters/outbound/<provider>/`.
2. Validate `provider_account.provider_key` inside sender.
3. Keep credentials retrieval indirection through `credentials_ref`.
4. Register sender in `ContainerFactory` sender registry map.
5. Ensure provider account records are available (`provider_accounts` table).
6. Update API/flow docs if behavior or payload mapping changes.

## Pattern For New Persistence Adapter
1. Implement relevant repository port(s) under infrastructure.
2. Keep mapping between ORM/document model and immutable domain entities explicit.
3. Preserve claim/update atomicity guarantees.
4. Update migration/model docs when schema/index behavior changes.

## Pattern For New Queue/Broker
1. Keep application use-case contracts unchanged when possible.
2. Encapsulate broker behavior in infrastructure adapter.
3. Document delivery guarantees (at-most-once, at-least-once) and retry ownership.
4. Update deployment docs (`docker-compose`, env vars) accordingly.

## Architecture Constraints
- Integrations must remain replaceable through ports.
- Use cases must not import SDK-specific clients.
- Runtime wiring remains centralized in bootstrap/container files.

## Validation Checklist
1. Unsupported provider/configuration paths fail with clear errors.
2. Retries and terminal failures remain observable in persisted state.
3. Idempotency is preserved across integration boundary failures.
4. Documentation includes extension steps and operational caveats.
