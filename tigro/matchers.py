"""
Набор базовых матчеров (Command / Callback / Predicate).
Можно писать свои, наследуясь от Matcher.
"""
from dataclasses import dataclass
from typing import Callable

from tigro.contracts import Matcher
from shared.schemas import TgEvent


@dataclass(slots=True)
class Command(Matcher):
    """Совпадение по точному тексту сообщения."""

    value: str

    def match(self, event: TgEvent) -> bool:
        return event.text == self.value


@dataclass(slots=True)
class Callback(Matcher):
    """Совпадение по callback_data (inline-кнопка)."""

    data: str

    def match(self, event: TgEvent) -> bool:
        return event.callback_data == self.data


class Predicate(Matcher):
    """Арбитрарное условие, передаём любую функцию."""

    def __init__(self, fn: Callable[[TgEvent], bool]) -> None:
        self._fn = fn

    def match(self, event: TgEvent) -> bool:  # noqa: D401
        return self._fn(event)
