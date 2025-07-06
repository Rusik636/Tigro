"""
Удобные декораторы, которые навешивают на хендлер
атрибут `__matcher__` для дальнейшей регистрации в Router.
"""
from tigro.matchers import Command, Callback, Predicate


def _attach_matcher(matcher):
    """Вспомогательная обёртка, чтобы избежать однотипного кода."""

    def decorator(func):
        func.__matcher__ = matcher
        return func

    return decorator


def command(cmd: str):
    """@command("/start")"""
    return _attach_matcher(Command(cmd))


def callback(data: str):
    """@callback("confirm_email")"""
    return _attach_matcher(Callback(data))


def message(predicate_fn):
    """
    @message(lambda ev: ev.text and ev.text.isdigit())
    """
    return _attach_matcher(Predicate(predicate_fn))
