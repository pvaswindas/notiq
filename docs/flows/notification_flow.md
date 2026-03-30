# Notification Flow

Canonical documentation for notification intake now lives in [core_flow.md](/home/aswin/code/unifiedbits/notiq/docs/flows/core_flow.md).

This file is retained for backward compatibility with existing links.

## Quick Summary
- Endpoint: `POST /notifications/send`
- Main use case: `SendNotificationUseCase`
- Output: persisted `delivery_jobs` rows + enqueue summary
- Next stage: worker processing in [processing_flow.md](/home/aswin/code/unifiedbits/notiq/docs/flows/processing_flow.md)
