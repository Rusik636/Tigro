from __future__ import annotations

"""Модуль рендереров Telegram-клавиатур под разные фреймворки.

SRP: Каждый рендерер отвечает только за преобразование абстрактного
     словаря `markup` в объект конкретной библиотеки.
OCP:  Чтобы поддержать новый фреймворк, достаточно реализовать
     новый класс, наследующий BaseRenderer.
LSP:  Все рендереры взаимозаменяемы (поддерживают метод render).
ISP:  Узкий интерфейс BaseRenderer не заставляет клиентов
     зависеть от деталей реализации.
DIP:  Клиент (gateway-бот) зависит от абстракции BaseRenderer,
     а не от конкретной библиотеки Aiogram.
"""

from typing import Protocol, Any, Dict, List, Optional

__all__ = ("BaseRenderer", "AiogramRenderer")


class BaseRenderer(Protocol):
    """Абстрактный интерфейс рендерера."""

    def render(self, markup: Optional[Dict[str, Any]]) -> Any:  # noqa: D401
        """Преобразовать словарь из TgResponse в объект фреймворка."""
        raise NotImplementedError


class AiogramRenderer:  # noqa: D101 – публичный API
    """Рендерер, возвращающий объекты из aiogram.types.*"""

    # Импорты внутри конструктора, чтобы не требовать aiogram
    # при использовании библиотеки в других фреймворках.
    def __init__(self) -> None:
        from aiogram.types import (
            InlineKeyboardMarkup,
            InlineKeyboardButton,
            ReplyKeyboardMarkup,
            KeyboardButton,
        )

        # Сохраняем ссылки на классы, чтобы использовать в render
        self._InlineKeyboardMarkup = InlineKeyboardMarkup
        self._InlineKeyboardButton = InlineKeyboardButton
        self._ReplyKeyboardMarkup = ReplyKeyboardMarkup
        self._KeyboardButton = KeyboardButton

    # ------------------------------------------------------------------
    # Основной метод
    # ------------------------------------------------------------------
    def render(self, markup: Optional[Dict[str, Any]]) -> Any:  # noqa: D401
        print(f"[🎨 Renderer] Рендерим клавиатуру: {markup}")
        if not markup:
            return None

        if "inline_keyboard" in markup:
            result = self._build_inline(markup["inline_keyboard"])  # type: ignore[arg-type]
            print(f"[🎨 Renderer] Создана inline клавиатура: {result}")
            return result
        if "keyboard" in markup:
            result = self._build_reply(markup["keyboard"])  # type: ignore[arg-type]
            print(f"[🎨 Renderer] Создана reply клавиатура: {result}")
            return result

        # Неизвестный тип – возвращаем None, чтобы не ломать работу
        print(f"[🎨 Renderer] Неизвестный тип клавиатуры: {markup}")
        return None

    # ------------------------------------------------------------------
    # Внутренние методы
    # ------------------------------------------------------------------
    def _build_inline(self, data: List[List[Dict[str, Any]]]):
        # data может быть как список рядов, так и dict с meta
        row_width = None
        if isinstance(data, dict):
            row_width = data.get("row_width")
            rows_source = data.get("inline_keyboard", [])
        else:
            rows_source = data

        buttons_rows = []
        for row in rows_source:
            btn_row = [
                self._InlineKeyboardButton(
                    text=btn.get("text", ""),
                    callback_data=btn.get("callback_data"),
                    url=btn.get("url"),
                )
                for btn in row
            ]
            buttons_rows.append(btn_row)

        return self._InlineKeyboardMarkup(
            inline_keyboard=buttons_rows,
            row_width=row_width or len(buttons_rows[0]) if buttons_rows else 3,
        )

    def _build_reply(self, data: List[List[Dict[str, Any]]]):
        buttons_rows = []
        for row in data:
            btn_row = [
                self._KeyboardButton(text=btn.get("text", ""))
                for btn in row
            ]
            buttons_rows.append(btn_row)

        return self._ReplyKeyboardMarkup(
            keyboard=buttons_rows,
            resize_keyboard=True,
        ) 