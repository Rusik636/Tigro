from __future__ import annotations

"""Автоматическая регистрация хендлеров в Router.

Позволяет избавиться от повторяющегося кода вида::

    for obj in globals().values():
        if callable(obj) and hasattr(obj, "__matcher__"):
            router.register(obj.__matcher__, obj)

Вместо этого достаточно вызвать::

    from tigro.discovery import autodiscover
    autodiscover(router)  # регистрирует все хендлеры текущего модуля

SOLID
-----
SRP  – модуль занимается только поиском и регистрацией хендлеров.
OCP  – при добавлении новых типов декораторов код не изменится.
LSP  – функции принимают Router и работают с его публичным API.
ISP  – узкий публичный интерфейс: register_handlers / autodiscover.
DIP  – зависит от абстракций Router/Matcher/Handler.
"""

from types import ModuleType
from typing import Mapping, Any
import inspect

from tigro.core import Router

__all__ = ("register_handlers", "autodiscover")


# ------------------------------------------------------------------
# Низкоуровневая функция
# ------------------------------------------------------------------

def register_handlers(router: Router, namespace: Mapping[str, Any]) -> int:  # noqa: D401
    """Найти в *namespace* все объекты с атрибутом ``__matcher__``.

    Зарегистрировать их в *router*.

    Возвращает количество зарегистрированных хендлеров.
    """
    count = 0
    for obj in namespace.values():
        if callable(obj) and hasattr(obj, "__matcher__"):
            router.register(getattr(obj, "__matcher__"), obj)  # type: ignore[arg-type]
            count += 1
    return count


# ------------------------------------------------------------------
# Удобная обёртка – определяет namespace автоматически
# ------------------------------------------------------------------

def autodiscover(router: Router) -> int:  # noqa: D401
    """Зарегистрировать хендлеры из модуля, вызвавшего функцию."""
    frame = inspect.currentframe()
    assert frame is not None  # для mypy
    caller_globals = frame.f_back.f_globals  # type: ignore[assignment]
    return register_handlers(router, caller_globals) 