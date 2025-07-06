"""
Ключевой модуль: Router, Context, ResponseCollector, ResponseDispatcher.

SOLID:
• SRP  – каждый класс имеет одну ответственность;
• OCP  – Router расширяется новыми Matcher / Handler без изменения кода;
• LSP  – любые Matcher взаимозаменяемы;
• ISP  – Router зависит от узких интерфейсов;
• DIP  – Router опирается на ResponsePublisher, а не на конкретный RabbitMQ.
"""
from __future__ import annotations

from typing import Iterable, Iterator, List, Dict, Any, Literal, cast

from shared.schemas import TgEvent, TgResponse
from tigro.contracts import (
    Matcher,
    Handler,
    ResponsePublisher,
    Middleware,
    Ctx,
)

__all__ = ("Router", "Context")


# ------------------------------------------------------------------ #
# 1. Коллектор ответов (Single Responsibility)                       #
# ------------------------------------------------------------------ #
class ResponseCollector:
    """Склад для ответов, формируемых в ходе обработки события."""

    __slots__ = ("_buffer",)

    def __init__(self) -> None:
        self._buffer: List[TgResponse] = []

    def add(self, response: TgResponse) -> None:
        """Поместить ответ в буфер."""
        self._buffer.append(response)

    def __iter__(self) -> Iterator[TgResponse]:
        return iter(self._buffer)


# ------------------------------------------------------------------ #
# 2. Диспетчер отправки (SRP + DIP)                                  #
# ------------------------------------------------------------------ #
class ResponseDispatcher:
    """
    Отвечает только за отправку буфера ответов конкретному пользователю.
    """

    __slots__ = ("_publisher",)

    def __init__(self, publisher: ResponsePublisher) -> None:
        self._publisher = publisher

    async def dispatch(
        self, user_id: int, responses: Iterable[TgResponse]
    ) -> None:
        for resp in responses:
            await self._publisher.publish(user_id, resp)
        return None


# ------------------------------------------------------------------ #
# 3. Контекст (SRP)                                                  #
# ------------------------------------------------------------------ #
class Context(Ctx):
    """
    Контекст доступен внутри хендлера.
    Формирует ответы, не знает о брокере.
    """

    __slots__ = ("_event", "_collector")

    def __init__(self, event: TgEvent, collector: ResponseCollector):
        self._event = event
        self._collector = collector

    # ---------- публичные методы ----------
    async def send_message(self, text: str, **kwargs: Any) -> None:
        """Сформировать команду «sendMessage»."""
        self._push("send_message", text, kwargs)
        return None

    async def edit_message(self, text: str, **kwargs: Any) -> None:
        """Сформировать команду «editMessageText»."""
        meta = {"edit_msg_id": kwargs.pop("message_id", self._event.message_id)}
        self._push("edit_message", text, kwargs, meta)
        return None


    # ---------- внутреннее ----------
    def _push(
        self,
        action: str,
        text: str,
        kwargs: Dict[str, Any],
        meta: Dict[str, Any] | None = None,
    ) -> None:
        self._collector.add(
            TgResponse(
                action=cast(
                    Literal[
                        "send_message",
                        "edit_message",
                        "answer_callback",
                        "none",
                    ],
                    action,
                ),
                text=text,
                metadata=meta or {},
                **kwargs,
            )
        )


# ------------------------------------------------------------------ #
# 4. Router (главный объект)                                         #
# ------------------------------------------------------------------ #
class Router:
    """
    Соединяет событие с подходящим хендлером и публикует ответы.

    Порядок работы:
    1. Выполняет `before`-middlewares.
    2. Находит первый Matcher, который подходит событию.
    3. Вызывает связанный Handler.
    4. Если не найден ни один Handler → отправляет «Команда не распознана».
    5. Публикует буфер ответов через ResponseDispatcher.
    6. Выполняет `after`-middlewares.
    """

    __slots__ = ("_routes", "_dispatcher", "_middlewares")

    def __init__(
        self,
        publisher: ResponsePublisher,
        middlewares: List[Middleware] | None = None,
    ) -> None:
        self._routes: List[tuple[Matcher, Handler]] = []
        self._dispatcher = ResponseDispatcher(publisher)
        self._middlewares = middlewares or []

    # ---------- регистрация ----------
    def register(self, matcher: Matcher, handler: Handler) -> None:
        """Добавить пару «Matcher → Handler»."""
        self._routes.append((matcher, handler))

    # ---------- основной метод ----------
    async def dispatch(self, event: TgEvent) -> None:
        """Обрабатывает одно событие TgEvent."""
        collector = ResponseCollector()
        ctx = Context(event, collector)

        # 1. Pre-middlewares
        for mw in self._middlewares:
            await mw.before(event)

        # 2. Поиск хендлера
        handled = False
        for matcher, handler in self._routes:
            if matcher.match(event):
                await handler(ctx)
                handled = True
                break

        if not handled:
            await ctx.send_message("Команда не распознана.")

        # 3. Публикация
        responses = list(collector)
        await self._dispatcher.dispatch(event.user_id, responses)

        # 4. Post-middlewares
        for mw in self._middlewares:
            await mw.after(event, responses)
