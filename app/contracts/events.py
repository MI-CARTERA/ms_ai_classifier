from dataclasses import dataclass


class EventNames:
    FILE_UPLOADED = "FILE_UPLOADED"
    AI_CLASSIFICATION_STARTED = "AI_CLASSIFICATION_STARTED"
    AI_CLASSIFICATION_COMPLETED = "AI_CLASSIFICATION_COMPLETED"
    AI_CLASSIFICATION_FAILED = "AI_CLASSIFICATION_FAILED"
    TRANSACTIONS_CLASSIFIED = "TRANSACTIONS_CLASSIFIED"


class RoutingKeys:
    FILE_UPLOADED = "files.file_uploaded"
    AI_CLASSIFICATION_STARTED = "ai.classification_started"
    AI_CLASSIFICATION_COMPLETED = "ai.classification_completed"
    AI_CLASSIFICATION_FAILED = "ai.classification_failed"
    TRANSACTIONS_CLASSIFIED = "ai.transactions_classified"


@dataclass(frozen=True)
class ExchangeContract:
    name: str = "mi_cartera_events"
