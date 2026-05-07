import json

import aio_pika

from app.contracts.events import ExchangeContract
from app.core.config import settings


class EventPublisher:
    def __init__(self) -> None:
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    async def _ensure_exchange(self) -> aio_pika.abc.AbstractExchange:
        if self._exchange is not None:
            return self._exchange

        self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(
            ExchangeContract().name,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        return self._exchange

    async def publish(self, routing_key: str, payload: dict) -> None:
        exchange = await self._ensure_exchange()
        message = aio_pika.Message(
            body=json.dumps(payload, default=str).encode("utf-8"),
            content_type="application/json",
        )
        await exchange.publish(message, routing_key=routing_key)

    async def close(self) -> None:
        if self._channel is not None:
            await self._channel.close()
        if self._connection is not None:
            await self._connection.close()
