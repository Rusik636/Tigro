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

from tigro.schemas import TgEvent, TgResponse
from tigro.contracts import (
    Matcher,
    Handler,
    ResponsePublisher,
    Middleware,
    Ctx,
    MessageCommand,
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
# 1.1 Команды сообщений (SRP, OCP, DIP)                             #
# ------------------------------------------------------------------ #
class SendMessageCommand(MessageCommand):
    def __init__(self, text: str, parse_mode: str = "", **kwargs: Any):
        self.text = text
        self.parse_mode = parse_mode
        self.kwargs = kwargs

    def to_response(self, event: TgEvent) -> TgResponse:
        return TgResponse(
            action="send_message",
            text=self.text,
            correlation_id=event.correlation_id,
            parse_mode=self.parse_mode,
            **self.kwargs,
        )

class EditMessageCommand(MessageCommand):
    def __init__(self, text: str, parse_mode: str = "", message_id: int | None = None, **kwargs: Any):
        self.text = text
        self.parse_mode = parse_mode
        self.message_id = message_id
        self.kwargs = kwargs

    def to_response(self, event: TgEvent) -> TgResponse:
        meta = {"edit_msg_id": self.message_id or event.message_id}
        return TgResponse(
            action="edit_message",
            text=self.text,
            correlation_id=event.correlation_id,
            metadata=meta,
            parse_mode=self.parse_mode,
            **self.kwargs,
        )


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
    async def send_message(self, text: str, parse_mode: str = "", **kwargs: Any) -> None:
        """Сформировать команду «sendMessage» с поддержкой parse_mode."""
        parse_mode = kwargs.pop("parse_mode", parse_mode)
        cmd = SendMessageCommand(text, parse_mode=parse_mode, **kwargs)
        self._push_command(cmd)
        return None

    async def edit_message(self, text: str, parse_mode: str = "", message_id: int | None = None, **kwargs: Any) -> None:
        """Сформировать команду «editMessageText» с поддержкой parse_mode."""
        parse_mode = kwargs.pop("parse_mode", parse_mode)
        cmd = EditMessageCommand(text, parse_mode=parse_mode, message_id=message_id, **kwargs)
        self._push_command(cmd)
        return None


    # ---------- внутреннее ----------
    def _push_command(self, cmd: MessageCommand) -> None:
        self._collector.add(cmd.to_response(self._event))


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
        handler_name = getattr(handler, '__name__', str(handler))
        print(f"[📝 Router] Регистрируем: {type(matcher).__name__} -> {handler_name}")
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
        print(f"[🔎 Router] Ищем обработчик для события: {event.event_type}, text='{event.text}', callback_data='{event.callback_data}'")
        for matcher, handler in self._routes:
            match_result = matcher.match(event)
            handler_name = getattr(handler, '__name__', str(handler))
            print(f"[🔎 Router] Проверяем {type(matcher).__name__} -> {handler_name}: {match_result}")
            if match_result:
                print(f"[🚀 Router] Handler {handler_name} выбран")
                await handler(ctx)
                handled = True
                break

        if not handled:
            print("[⚠️ Router] Хендлер не найден, отправляем сообщение по умолчанию")
            await ctx.send_message("Команда не распознана.")

        # 3. Публикация
        responses = list(collector)
        await self._dispatcher.dispatch(event.user_id, responses)

        # 4. Post-middlewares
        for mw in self._middlewares:
            await mw.after(event, responses)
