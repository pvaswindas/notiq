# Adding New Integration

## Scope
Use this guide for new provider, persistence, queue, or auth-adjacent integrations.

## New Provider Integration Pattern
1. Implement the sender behind `NotificationSenderPort`.
2. Define the expected `credentials` JSON shape and validate it in `ProviderConfigurationValidator`.
3. Validate provider and account compatibility inside the adapter.
4. Keep credential source handling in provider-account abstractions.
5. Register the sender in container wiring.
6. Add or update tests for unsupported provider paths and transient failure handling.
7. Update API and flow docs where behavior changes.

## New Persistence Integration Pattern
1. Implement repository ports with explicit mappings.
2. Preserve atomicity for dedupe claims and job transitions.
3. Keep domain objects free from persistence model leakage.
4. Document schema and index implications.

## New Queue Or Broker Pattern
1. Preserve use-case contracts where possible.
2. Encapsulate broker runtime details in infrastructure.
3. Document delivery guarantees and retry ownership.
4. Update deployment and environment guidance.

## Compatibility `/events` Integrations
1. Keep compatibility mapping limited to request-shape translation.
2. Reuse the modular notification pipeline instead of introducing a parallel queueing path.
3. Preserve authentication and workspace scoping behavior for existing clients.

## Guardrails
- Do not couple use cases to SDK clients.
- Do not bypass composition roots for runtime wiring.
- Do not merge incompatible semantics between primary and compatibility flows without explicit migration planning.
- Do not hide provider-specific credential assumptions in undocumented dictionary keys.
