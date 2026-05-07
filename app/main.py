from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.classification_jobs import router as classification_jobs_router
from app.api.routes.health import router as health_router
from app.core.config import settings
from app.db.session import init_db
from app.messaging.consumer import RabbitConsumer
from app.messaging.publisher import EventPublisher
from app.repositories.classification_job_repository import ClassificationJobRepository
from app.services.classification_pipeline import ClassificationPipeline
from app.services.openai_classifier import OpenAIStatementClassifier
from app.services.pdf_extractor import PdfExtractor
from app.services.rest_callbacks import RestCallbackClient


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()

    publisher = EventPublisher()
    callbacks = RestCallbackClient()
    pipeline = ClassificationPipeline(
        repository=ClassificationJobRepository(),
        extractor=PdfExtractor(max_pages=settings.openai_max_pdf_pages),
        classifier=OpenAIStatementClassifier(),
        publisher=publisher,
        callbacks=callbacks,
    )
    consumer = RabbitConsumer(pipeline=pipeline)
    await consumer.start()

    try:
        yield
    finally:
        await consumer.close()
        await publisher.close()
        await callbacks.close()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.include_router(health_router)
app.include_router(classification_jobs_router, prefix="/api/v1")
