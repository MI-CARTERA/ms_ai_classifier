from datetime import datetime, timezone
from uuid import uuid4


def build_event(
    *,
    event_name: str,
    producer: str,
    correlation_id: str | None,
    causation_id: str | None,
    payload: dict,
) -> dict:
    return {
        "event_name": event_name,
        "event_version": 1,
        "event_id": str(uuid4()),
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "producer": producer,
        "correlation_id": correlation_id,
        "causation_id": causation_id,
        "payload": payload,
    }
