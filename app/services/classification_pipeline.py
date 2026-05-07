from datetime import datetime, timezone
from uuid import uuid4

from app.contracts.events import EventNames, RoutingKeys
from app.messaging.publisher import EventPublisher
from app.repositories.classification_job_repository import ClassificationJobRepository
from app.schemas.classification import ClassificationOutput
from app.schemas.events import FileUploadedEvent
from app.services.openai_classifier import OpenAIStatementClassifier
from app.services.pdf_extractor import PdfExtractor
from app.services.rest_callbacks import RestCallbackClient


class ClassificationPipeline:
    def __init__(
        self,
        *,
        repository: ClassificationJobRepository,
        extractor: PdfExtractor,
        classifier: OpenAIStatementClassifier,
        publisher: EventPublisher,
        callbacks: RestCallbackClient,
    ) -> None:
        self.repository = repository
        self.extractor = extractor
        self.classifier = classifier
        self.publisher = publisher
        self.callbacks = callbacks

    async def handle_file_uploaded(self, event: FileUploadedEvent) -> None:
        payload = event.payload
        job_id = uuid4().hex

        self.repository.create_job(
            job_id=job_id,
            file_id=payload.file_id,
            user_id=payload.user_id,
            bank_account_id=payload.bank_account_id,
            file_name=payload.file_name,
            storage_path=payload.storage_path,
            status="received",
        )

        try:
            pdf_path, extracted_text = self.extractor.extract_text(payload.storage_path)
            self.repository.mark_processing(job_id, extracted_text)
            result = self.classifier.classify(pdf_path=pdf_path, extracted_text=extracted_text)
            normalized = self._classification_to_dict(result)
            self.repository.mark_succeeded(job_id, normalized)

            success_event = {
                "event_name": EventNames.TRANSACTIONS_CLASSIFIED,
                "event_version": 1,
                "event_id": str(uuid4()),
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "producer": "ms_ai_classifier",
                "correlation_id": event.correlation_id or job_id,
                "causation_id": str(event.event_id),
                "payload": {
                    "file_id": payload.file_id,
                    "user_id": payload.user_id,
                    "bank_account_id": payload.bank_account_id,
                    "job_id": job_id,
                    "statement_period": normalized.get("statement_period"),
                    "currency": normalized.get("currency"),
                    "classifier": "openai_structured_outputs",
                    "extraction_summary": normalized.get("extraction_summary"),
                    "transactions": normalized.get("transactions", []),
                },
            }
            await self.publisher.publish(RoutingKeys.TRANSACTIONS_CLASSIFIED, success_event)
            await self.callbacks.notify_transactions_status(success_event)
            await self.callbacks.notify_files_status(
                {"file_id": payload.file_id, "job_id": job_id, "status": "classified"}
            )
        except Exception as exc:
            self.repository.mark_failed(job_id, str(exc))
            failure_event = {
                "event_name": EventNames.AI_CLASSIFICATION_FAILED,
                "event_version": 1,
                "event_id": str(uuid4()),
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "producer": "ms_ai_classifier",
                "correlation_id": event.correlation_id or job_id,
                "causation_id": str(event.event_id),
                "payload": {
                    "file_id": payload.file_id,
                    "user_id": payload.user_id,
                    "bank_account_id": payload.bank_account_id,
                    "job_id": job_id,
                    "error_code": "CLASSIFICATION_FAILED",
                    "error_message": str(exc),
                    "retryable": True,
                    "failure_stage": "classification_pipeline",
                },
            }
            await self.publisher.publish(RoutingKeys.AI_CLASSIFICATION_FAILED, failure_event)
            await self.callbacks.notify_files_status(
                {
                    "file_id": payload.file_id,
                    "job_id": job_id,
                    "status": "failed",
                    "error": str(exc),
                }
            )

    @staticmethod
    def _classification_to_dict(result: ClassificationOutput) -> dict:
        return result.model_dump(mode="json")
