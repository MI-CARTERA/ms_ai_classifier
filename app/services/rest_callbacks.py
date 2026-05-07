import httpx

from app.core.config import settings


class RestCallbackClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=10.0)

    async def notify_files_status(self, payload: dict) -> None:
        if settings.files_status_callback_url is None:
            return
        await self._client.post(settings.files_status_callback_url, json=payload)

    async def notify_transactions_status(self, payload: dict) -> None:
        if settings.transactions_status_callback_url is None:
            return
        await self._client.post(settings.transactions_status_callback_url, json=payload)

    async def close(self) -> None:
        await self._client.aclose()
