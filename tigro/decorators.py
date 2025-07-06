"""
Удобные декораторы, которые навешивают на хендлер
атрибут `__matcher__` для дальнейшей регистрации в Router.
"""
from typing import Awaitable, Callable, TypeVar

from tigro.matchers import Callback, Command, Predicate
from tigro.contracts import Matcher
from tigro.core import Context
from shared.schemas import TgEvent

F = TypeVar("F", bound=Callable[[Context], Awaitable[None]])


def _attach_matcher(matcher: Matcher) -> Callable[[F], F]:
    """Прикрепить Matcher к функции-хендлеру."""

    def decorator(func: F) -> F:
        setattr(func, "__matcher__", matcher)
        return func

    return decorator


def command(cmd: str) -> Callable[[F], F]:
    """@command("/start")"""
    return _attach_matcher(Command(cmd))


def callback(data: str) -> Callable[[F], F]:
    """@callback("confirm_email")"""
    return _attach_matcher(Callback(data))


def message(predicate_fn: Callable[[TgEvent], bool]) -> Callable[[F], F]:
    """
    @message(lambda ev: ev.text and ev.text.isdigit())
    """
    return _attach_matcher(Predicate(predicate_fn))
