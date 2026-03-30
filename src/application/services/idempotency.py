import hashlib
import json

from src.domain.entities.channel import Channel
from src.domain.entities.event import Event


def generate_idempotency_key(event: Event, channel: Channel) -> str:
    payload_json = json.dumps(event.payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    raw_key = f"{event.workspace_id}:{event.event_type}:{payload_hash}:{channel.id}"
    digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return f"idempotency:{digest}"
