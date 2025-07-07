from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict
from typing import Dict

from faststream.rabbit import RabbitBroker

from tigro.schemas import TgEvent, TgResponse

__all__ = ("RpcClient",)


class RpcClient:
    """Простой RPC-клиент поверх RabbitMQ.

    1. Автоматически подписывается на очередь `event.user.response`.
    2. Хранит таблицу pending-futures по `correlation_id`.
    3. Предоставляет метод `call` для отправки события и ожидания ответа.
    """

    def __init__(self, broker_url: str = "amqp://guest:guest@localhost/") -> None:
        self._broker = RabbitBroker(broker_url)
        self._pending: Dict[str, asyncio.Future] = defaultdict(asyncio.Future)

        # Регистрация подписчика до подключения
        @self._broker.subscriber("event.user.response")
        async def _listener(msg: Dict):  # noqa: WPS430
            cid = msg.get("correlation_id")
            fut = self._pending.get(cid)
            if fut and not fut.done():
                fut.set_result(msg)

    # ------------------------------------------------------------------
    # Публичные методы
    # ------------------------------------------------------------------
    async def start(self) -> None:
        """Установить соединение и запустить длительную обработку."""
        await self._broker.start()

    async def call(self, event: TgEvent, timeout: float = 5.0) -> TgResponse:
        """Отправить событие и дождаться ответа."""
        cid = str(uuid.uuid4())
        event.correlation_id = cid

        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        self._pending[cid] = fut

        await self._broker.publish(
            event.model_dump(),
            routing_key="event.user.input",
        )

        try:
            raw = await asyncio.wait_for(fut, timeout)
            return TgResponse(**raw)
        finally:
            self._pending.pop(cid, None) 