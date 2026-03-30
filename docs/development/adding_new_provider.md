# Adding a New Provider

## Goal
Integrate a new outbound provider without changing core domain behavior.

## Steps
1. Create outbound adapter class under:
- `src/modules/notifications/adapters/outbound/<provider>/<provider>_notifier.py`
2. Implement `NotificationSenderPort.send(job, provider_account)`.
3. Validate provider/account compatibility in sender.
4. Register adapter in `ContainerFactory` sender registry map.
5. Ensure provider accounts can be seeded/configured in `provider_accounts` table (`provider_key` + defaults).
6. Add/update docs in `docs/api` and `docs/flows` if behavior differs.

## Rules to Follow
- Do not add provider SDK logic inside use cases.
- Keep retry classification centralized in `ProcessDeliveryJobUseCase` unless taxonomy extension is deliberate.
- Use `provider_account.credentials_ref` as indirection; do not store raw secrets in domain entities.
- Maintain idempotency and status transition semantics.

## Validation Checklist
- Sender resolves by new `provider_key`.
- Workspace/default account resolution works.
- Successful delivery sets `SUCCESS`.
- Transient failure retries as expected.
- Permanent failure sets `FAILED`.
