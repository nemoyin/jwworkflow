"""SSE (Server-Sent Events) event data model for workflow execution."""

import json
from datetime import datetime, timezone


class SSEEvent:
    """SSE 事件数据模型

    Represents a single event emitted during workflow execution.
    Each event carries a type, a free-form data dict, and a UTC timestamp.
    """

    def __init__(self, event_type: str, data: dict):
        self.event_type = event_type
        self.data = data
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp,
        }
