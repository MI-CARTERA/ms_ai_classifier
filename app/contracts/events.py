from dataclasses import dataclass


class EventNames:
    FILE_UPLOADED = "FILE_UPLOADED"
    TRANSACTIONS_CLASSIFIED = "TRANSACTIONS_CLASSIFIED"
    AI_CLASSIFICATION_FAILED = "AI_CLASSIFICATION_FAILED"


class RoutingKeys:
    FILE_UPLOADED = "files.file_uploaded"
    TRANSACTIONS_CLASSIFIED = "ai.transactions_classified"
    AI_CLASSIFICATION_FAILED = "ai.classification_failed"


@dataclass(frozen=True)
class ExchangeContract:
    name: str = "mi_cartera_events"
