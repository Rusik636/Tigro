"""
Конрактные (абстрактные) интерфейсы Tigro.

SOLID:
• ISP — каждый интерфейс узко сфокусирован.
• DIP — более высокие уровни работают с этими абстракциями,
  а не с конкретными реализациями (RabbitMQ, aiogram и т.д.).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, Callable, Awaitable, Sequence

from shared.schemas import TgEvent, TgResponse


# ---------------- Транспортные абстракции ----------------
class ResponsePublisher(Protocol):
    """
    Публикует сформированный TgResponse в персональную очередь
    вида «event.user.response.{user_id}».
    """

    async def publish(self, user_id: int, response: TgResponse) -> None: ...


class EventSource(Protocol):
    """
    Источник входящих событий от gateway_bot.
    Не используется напрямую в библиотеках микросервисов,
    но оставлен для возможных расширений.
    """

    async def subscribe(
        self, handler: Callable[[TgEvent], Awaitable[None]]
    ) -> None: ...


# ---------------- Высокоуровневые абстракции ----------------
class Handler(ABC):
    """Пользовательский хендлер."""

    @abstractmethod
    async def __call__(self, ctx: "Ctx") -> None: ...


class Matcher(ABC):
    """Определяет, подходит ли событие этому хендлеру."""

    @abstractmethod
    def match(self, event: TgEvent) -> bool: ...


class Middleware(ABC):
    """Дополнительные фильтры / логирование / метрики."""

    async def before(self, event: TgEvent) -> None: ...  # noqa: D401
    async def after(
        self, event: TgEvent, responses: Sequence[TgResponse]
    ) -> None: ...  # noqa: D401


class Ctx(ABC):
    """
    Интерфейс контекста, который получает каждый хендлер.

    Пользователь видит только send_message / edit_message,
    а транспортные детали скрыты.
    """

    @abstractmethod
    async def send_message(self, text: str, **kwargs) -> None: ...

    @abstractmethod
    async def edit_message(self, text: str, **kwargs) -> None: ...

    @abstractmethod
    async def flush(self) -> None: ...
