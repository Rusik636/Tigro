from __future__ import annotations

"""Инфраструктура для много-модульности (подобно FastAPI APIRouter).

Использование::

    # users.py
    from tigro import command, Context, autodiscover
    from tigro.modules import ModuleRouter

    router = ModuleRouter()
    autodiscover(router)  # регистрирует handlers текущего файла

    # main.py
    from tigro.modules import include_router
    from users import router as users_router

    main_router = Router(publisher=RabbitPublisher(broker))
    include_router(main_router, users_router)

После этого все хендлеры из ``users.py`` будут работать внутри ``main_router``.

SOLID
-----
SRP  – ModuleRouter только собирает маршруты.
OCP  – добавление нового модуля не требует изменений в core Router.
LSP  – include_router работает с любым Router, в т.ч. ModuleRouter.
ISP  – публичный интерфейс максимально узкий.
DIP  – логика объединения вынесена в функцию, Router остаётся неизменным.
"""

from typing import List, Tuple, Callable, Awaitable, TypeVar

from tigro.core import Router
from tigro.contracts import Matcher, Handler, ResponsePublisher
from tigro.matchers import Command as _Command, Callback as _Callback, Predicate as _Predicate
from tigro.core import Context

__all__ = ("ModuleRouter", "include_router")


class _NullPublisher(ResponsePublisher):
    """Паблишер-заглушка: используется в ModuleRouter."""

    async def publish(self, user_id: int, response):  # type: ignore[override]
        # Ничего не делаем, ModuleRouter не отправляет ответы напрямую
        return None


class ModuleRouter(Router):
    """Router, предназначенный только для группировки хендлеров."""

    def __init__(self):
        super().__init__(publisher=_NullPublisher())

    # ------------------------------------------------------------------
    # Декораторы в стиле FastAPI / Aiogram
    # ------------------------------------------------------------------
    def command(self, cmd: str) -> Callable[[Callable[[Context], Awaitable[None]]], Callable[[Context], Awaitable[None]]]:  # noqa: D401
        """@router.command("/start")"""

        def decorator(func: Callable[[Context], Awaitable[None]]) -> Callable[[Context], Awaitable[None]]:
            self.register(_Command(cmd), func)
            return func

        return decorator

    def callback(self, data: str) -> Callable[[Callable[[Context], Awaitable[None]]], Callable[[Context], Awaitable[None]]]:  # noqa: D401
        """@router.callback("confirm_email")"""

        def decorator(func: Callable[[Context], Awaitable[None]]) -> Callable[[Context], Awaitable[None]]:
            self.register(_Callback(data), func)
            return func

        return decorator

    def message(self, predicate: Callable[["TgEvent"], bool]) -> Callable[[Callable[[Context], Awaitable[None]]], Callable[[Context], Awaitable[None]]]:  # noqa: D401
        """@router.message(lambda ev: ev.text.isdigit())"""

        def decorator(func: Callable[[Context], Awaitable[None]]) -> Callable[[Context], Awaitable[None]]:
            self.register(_Predicate(predicate), func)
            return func

        return decorator


# ------------------------------------------------------------------
# Функция объединения роутеров
# ------------------------------------------------------------------

def include_router(parent: Router, child: Router) -> int:  # noqa: D401
    """Скопировать все маршруты из *child* в *parent*.

    Возвращает количество переданных маршрутов.
    """
    # Доступ к _routes не нарушает OCP, потому что это friend-функция
    routes: List[Tuple[Matcher, Handler]] = getattr(child, "_routes", [])  # type: ignore[assignment]
    for matcher, handler in routes:
        parent.register(matcher, handler)
    return len(routes) 