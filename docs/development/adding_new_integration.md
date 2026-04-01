# Adding New Integration

## Scope
Use this guide for new provider, persistence, queue, or auth-adjacent integrations.

## New Provider Integration Pattern
1. Implement sender behind `NotificationSenderPort`.
2. Validate provider/account compatibility in adapter.
3. Keep credential source handling in provider-account abstractions.
4. Register sender in container wiring.
5. Add/update tests for unsupported provider paths.
6. Update API + flow docs where behavior changes.

## New Persistence Integration Pattern
1. Implement repository ports with explicit mappings.
2. Preserve atomicity for dedupe claims and job transitions.
3. Keep domain objects free from persistence model leakage.
4. Document schema/index implications.

## New Queue/Broker Pattern
1. Preserve use-case contracts where possible.
2. Encapsulate broker runtime details in infrastructure.
3. Document delivery guarantees and retry ownership.
4. Update deployment/env guidance.

## Compatibility `/events` Integrations
1. Keep rate-limit policy selection in compatibility application services.
2. Keep backend enforcement in infrastructure adapters.
3. Preserve retry safety (release idempotency claim before requeue/retry failure).

## Guardrails
- Do not couple use cases to SDK clients.
- Do not bypass composition roots for runtime wiring.
- Do not merge incompatible semantics between primary and compatibility flows without explicit migration planning.
