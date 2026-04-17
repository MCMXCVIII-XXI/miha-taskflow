from enum import Enum


class OutboxEventType(Enum):
    """Event types for outbox."""

    CREATED = "CREATED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"


class OutboxStatus(Enum):
    """Status events for outbox."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
