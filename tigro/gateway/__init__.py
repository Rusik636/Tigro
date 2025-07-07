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
from .aiogram_gateway import AiogramGateway
# from .telebot_gateway import TelebotGateway  # если реализовано

GATEWAY_REGISTRY = {
    "aiogram": AiogramGateway,
    # "telebot": TelebotGateway,
}

def get_gateway_class(framework: str):
    try:
        return GATEWAY_REGISTRY[framework]
    except KeyError:
        raise ValueError(f"Gateway for framework '{framework}' is not implemented")

def run_gateway(token: str, broker_url: str = "amqp://guest:guest@localhost/", framework: str = "aiogram"):
    GatewayClass = get_gateway_class(framework)
    gateway = GatewayClass(token=token, broker_url=broker_url)
    import asyncio
    asyncio.run(gateway.run())

__all__ = ("AiogramGateway", "run_gateway", "RpcClient") 