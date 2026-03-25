import hashlib
import json
from typing import Any

from src.modules.notifications.domain.entities.event import Event
from src.modules.notifications.domain.value_objects.event_fingerprint import EventFingerprint


class IdempotencyService:
    """
    Purpose:
    - Generate deterministic fingerprints for deduplication.

    Responsibilities:
    - Convert event identity and payload into a stable hash.

    Inputs:
    - Event

    Outputs:
    - EventFingerprint

    Constraints:
    - Must produce deterministic output for equivalent semantic payloads.
    """

    def create_event_fingerprint(self, event: Event) -> EventFingerprint:
        """
        Purpose:
        - Produce idempotency fingerprint for an event.

        Responsibilities:
        - Canonicalize payload and compute SHA-256 hash.

        Inputs:
        - event: Event

        Outputs:
        - EventFingerprint

        Constraints:
        - Payload must be JSON-serializable.
        """

        canonical_payload = json.dumps(event.payload, sort_keys=True, separators=(",", ":"))
        raw_value = f"{event.workspace_id}:{event.event_id}:{event.event_name}:{canonical_payload}"
        digest = hashlib.sha256(raw_value.encode("utf-8")).hexdigest()
        return EventFingerprint(value=digest)

    def create_channel_fingerprint(self, event_fingerprint: EventFingerprint, channel_id: str) -> EventFingerprint:
        """
        Purpose:
        - Produce per-channel dedupe key from event fingerprint.

        Responsibilities:
        - Derive a deterministic child fingerprint scoped to channel.

        Inputs:
        - event_fingerprint: EventFingerprint
        - channel_id: str

        Outputs:
        - EventFingerprint

        Constraints:
        - Channel identifier must be non-empty.
        """

        raw_value = f"{event_fingerprint.value}:{channel_id}"
        digest = hashlib.sha256(raw_value.encode("utf-8")).hexdigest()
        return EventFingerprint(value=digest)
