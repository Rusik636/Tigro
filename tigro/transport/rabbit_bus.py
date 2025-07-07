"""
Адаптер RabbitMQ → ResponsePublisher.

Отвечает только за отправку сообщений в правильную очередь,
не содержит бизнес-логики.
"""
from faststream.rabbit import RabbitBroker  # type: ignore

from shared.schemas import TgResponse
from tigro.contracts import ResponsePublisher


class RabbitPublisher(ResponsePublisher):
    """
    Публикует TgResponse в очередь `event.user.response.{user_id}`.

    Можно заменить на KafkaPublisher, если реализовать
    тот же интерфейс publish(user_id, response).
    """

    def __init__(self, broker: RabbitBroker) -> None:
        self._broker = broker

    async def publish(self, user_id: int, response: TgResponse) -> None:  # noqa: D401
        await self._broker.publish(
            response.dict(),
            # Отправляем все ответы в единую очередь, а сопоставление выполняем по correlation_id
            # Это упрощает настройку Gateway-бота и избавляет от необходимости динамически
            # создавать очереди под каждого пользователя.
            routing_key="event.user.response",
        )
        # 👇 Отладочная информация — видно, что ответ отправлен в брокер
        print(
            f"[🐇 RabbitPublisher] Ответ отправлен | user_id={user_id} | correlation_id={response.correlation_id}")
        return None
