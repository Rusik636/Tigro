"""
🐯 Tigro — микробиблиотека для построения Telegram-ботов
в микросервисной архитектуре (RabbitMQ / FastStream).

Здесь экспортируются только публичные сущности,
которые нужны пользователю: Router, Context, декораторы.
"""
from tigro.core import Router, Context                 # noqa: F401
from tigro.decorators import command, callback, message  # noqa: F401
from tigro.discovery import autodiscover  # noqa: F401
from tigro.modules import ModuleRouter, include_router  # noqa: F401
from tigro.keyboard import cb_btn, url_btn, inline_kb, reply_kb, inline_kb_grid  # noqa: F401

__all__ = (
    "Router",
    "Context",
    "command",
    "callback",
    "message",
    "reply_kb",
    "inline_kb_grid",
)
