import json
import logging

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from app.contracts.events import ExchangeContract
from app.core.config import settings
from app.schemas.events import FileUploadedEvent
from app.services.classification_pipeline import ClassificationPipeline

logger = logging.getLogger(__name__)


class RabbitConsumer:
    def __init__(self, pipeline: ClassificationPipeline) -> None:
        self.pipeline = pipeline
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._queue: aio_pika.abc.AbstractQueue | None = None

    async def start(self) -> None:
        self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)

        exchange = await self._channel.declare_exchange(
            ExchangeContract().name,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        self._queue = await self._channel.declare_queue(settings.rabbitmq_queue, durable=True)

        for routing_key in settings.rabbitmq_routing_key_list:
            await self._queue.bind(exchange, routing_key)

        await self._queue.consume(self._on_message, no_ack=False)
        logger.info("RabbitMQ consumer started on queue %s", settings.rabbitmq_queue)

    async def _on_message(self, message: AbstractIncomingMessage) -> None:
        async with message.process(requeue=False):
            payload = json.loads(message.body.decode("utf-8"))
            event = FileUploadedEvent.model_validate(payload)
            await self.pipeline.handle_file_uploaded(event)

    async def close(self) -> None:
        if self._channel is not None:
            await self._channel.close()
        if self._connection is not None:
            await self._connection.close()
