from __future__ import annotations

"""Gateway-подсистема Tigro.

Содержит готовую реализацию Telegram-бота-шлюза, который:
1) Принимает события от Telegram (aiogram).
2) Преобразует их в `TgEvent`.
3) Отправляет RPC-запрос в очередь `event.user.input`.
4) Ожидает ответ (с сохранением `correlation_id`).
5) Отправляет сообщение пользователю, рендеря клавиатуры.

SRP  – каждый класс отвечает за один аспект (RPC, Gateway).
OCP  – можно добавить поддержку другого фреймворка, создав новый Renderer или Gateway.
LSP  – все Gateway совместимы по интерфейсу run().
ISP  – пользователю нужен только `run_gateway`.
DIP  – Gateway зависит от абстракций Renderer, RpcTransport.
"""

from .rpc import RpcClient  # noqa: F401 – re-export
from .aiogram_gateway import AiogramGateway, run_gateway  # noqa: F401

__all__ = ("AiogramGateway", "run_gateway", "RpcClient") 