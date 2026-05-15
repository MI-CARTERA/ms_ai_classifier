import asyncio
from uuid import uuid4

from app.contracts.events import EventNames, RoutingKeys
from app.messaging.publisher import EventPublisher
from app.repositories.classification_job_repository import ClassificationJobRepository
from app.schemas.classification import StatementClassificationResult
from app.schemas.events import FileUploadedEvent
from app.services.event_factory import build_event
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
            tenant_id=payload.tenant_id,
            file_name=payload.file_name,
            storage_path=payload.storage_path,
            status="received",
        )

        started_event = build_event(
            event_name=EventNames.AI_CLASSIFICATION_STARTED,
            producer="ms_ai_classifier",
            correlation_id=event.correlation_id or job_id,
            causation_id=str(event.event_id),
            payload={
                "file_id": payload.file_id,
                "user_id": payload.user_id,
                "bank_account_id": payload.bank_account_id,
                "tenant_id": payload.tenant_id,
                "job_id": job_id,
                "file_name": payload.file_name,
            },
        )
        await self.publisher.publish(RoutingKeys.AI_CLASSIFICATION_STARTED, started_event)
        self.repository.update_job_status(job_id, status="started")

        try:
            extraction = await asyncio.to_thread(self.extractor.extract, payload.storage_path)
            self.repository.store_extraction(
                job_id,
                extracted_text=extraction.extracted_text,
                extraction_summary=extraction.extraction_summary,
                currency=extraction.currency,
                transactions=extraction.transactions,
            )
            self.repository.update_job_status(job_id, status="classifying")

            result = await asyncio.to_thread(
                self.classifier.classify,
                extraction=extraction,
                file_name=payload.file_name,
                statement_hint=payload.statement_hint,
            )
            self.repository.store_classifications(
                job_id,
                classifier_name=self.classifier.classifier_name,
                extraction_summary=result.extraction_summary,
                currency=result.currency,
                classifications=result.transactions,
            )

            completed_event = build_completed_event(
                result=result,
                payload=payload,
                job_id=job_id,
                correlation_id=event.correlation_id or job_id,
                causation_id=str(event.event_id),
                classifier_name=self.classifier.classifier_name,
            )
            transactions_event = build_transactions_event(
                result=result,
                payload=payload,
                job_id=job_id,
                correlation_id=event.correlation_id or job_id,
                causation_id=str(event.event_id),
                classifier_name=self.classifier.classifier_name,
            )

            await self.publisher.publish(RoutingKeys.AI_CLASSIFICATION_COMPLETED, completed_event)
            await self.publisher.publish(RoutingKeys.TRANSACTIONS_CLASSIFIED, transactions_event)
            await self.callbacks.notify_transactions_status(transactions_event)
            await self.callbacks.notify_files_status(
                {"file_id": payload.file_id, "job_id": job_id, "status": "classified"}
            )
        except Exception as exc:
            self.repository.mark_failed(job_id, str(exc))
            failure_event = build_event(
                event_name=EventNames.AI_CLASSIFICATION_FAILED,
                producer="ms_ai_classifier",
                correlation_id=event.correlation_id or job_id,
                causation_id=str(event.event_id),
                payload={
                    "file_id": payload.file_id,
                    "user_id": payload.user_id,
                    "bank_account_id": payload.bank_account_id,
                    "tenant_id": payload.tenant_id,
                    "job_id": job_id,
                    "error_code": "CLASSIFICATION_FAILED",
                    "error_message": str(exc),
                    "retryable": True,
                    "failure_stage": "classification_pipeline",
                },
            )
            await self.publisher.publish(RoutingKeys.AI_CLASSIFICATION_FAILED, failure_event)
            await self.callbacks.notify_files_status(
                {
                    "file_id": payload.file_id,
                    "job_id": job_id,
                    "status": "failed",
                    "error": str(exc),
                }
            )


def build_completed_event(
    *,
    result: StatementClassificationResult,
    payload,
    job_id: str,
    correlation_id: str,
    causation_id: str,
    classifier_name: str,
) -> dict:
    review_required_count = sum(1 for item in result.transactions if item.needs_review)
    return build_event(
        event_name=EventNames.AI_CLASSIFICATION_COMPLETED,
        producer="ms_ai_classifier",
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload={
            "file_id": payload.file_id,
            "user_id": payload.user_id,
            "bank_account_id": payload.bank_account_id,
            "tenant_id": payload.tenant_id,
            "job_id": job_id,
            "total_transactions": len(result.transactions),
            "review_required_count": review_required_count,
            "currency": result.currency,
            "classifier": classifier_name,
        },
    )


def build_transactions_event(
    *,
    result: StatementClassificationResult,
    payload,
    job_id: str,
    correlation_id: str,
    causation_id: str,
    classifier_name: str,
) -> dict:
    return build_event(
        event_name=EventNames.TRANSACTIONS_CLASSIFIED,
        producer="ms_ai_classifier",
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload={
            "file_id": payload.file_id,
            "user_id": payload.user_id,
            "bank_account_id": payload.bank_account_id,
            "tenant_id": payload.tenant_id,
            "job_id": job_id,
            "statement_period": result.statement_period.model_dump() if result.statement_period else None,
            "currency": result.currency,
            "classifier": classifier_name,
            "extraction_summary": result.extraction_summary,
            "transactions": [item.model_dump(mode="json") for item in result.transactions],
        },
    )
