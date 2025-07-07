from __future__ import annotations

import asyncio
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from tigro.schemas import TgEvent
from tigro.renderers import AiogramRenderer

from .rpc import RpcClient

__all__ = ("AiogramGateway", "run_gateway")


class AiogramGateway:
    """Gateway-бот на базе Aiogram и Tigro."""

    def __init__(
        self,
        token: str,
        broker_url: str = "amqp://guest:guest@localhost/",
        renderer: Optional[AiogramRenderer] = None,
    ) -> None:
        self._bot = Bot(token)
        self._dp = Dispatcher(storage=MemoryStorage())
        self._rpc = RpcClient(broker_url)
        self._renderer = renderer or AiogramRenderer()

        # Регистрируем универсальный message-handler
        self._dp.message()(self._on_message)
        self._dp.callback_query()(self._on_callback)
        print("[🔧 Gateway] Обработчики зарегистрированы: message и callback_query")

    # ------------------------------------------------------------------
    # Публичный API
    # ------------------------------------------------------------------
    async def run(self) -> None:  # noqa: D401
        print("[🚀 Gateway] Запуск бота...")
        await self._rpc.start()
        print("[🚀 Gateway] RPC клиент запущен, начинаем polling...")
        await self._dp.start_polling(self._bot)

    # ------------------------------------------------------------------
    # Внутренние методы
    # ------------------------------------------------------------------
    async def _on_message(self, message: Message, state: FSMContext):  # noqa: WPS110
        print(f"[📨 Gateway] Получено сообщение: {message.text!r} от пользователя {message.from_user.id}")
        # 1. Формируем TgEvent
        event = TgEvent(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=message.text,
            state=await state.get_state(),
            event_type="message",
        )

        # 2. RPC-вызов
        try:
            resp = await self._rpc.call(event)
        except asyncio.TimeoutError:
            return await message.answer("⚠️ Сервис не ответил")

        # 3. Ответ пользователю
        if resp.action == "send_message":
            await message.answer(
                resp.text or "",
                reply_markup=self._renderer.render(resp.markup),
                parse_mode=resp.parse_mode,
            )

    async def _on_callback(self, cq: CallbackQuery, state: FSMContext):  # noqa: WPS110
        print(f"[📲 Gateway] Callback data={cq.data!r} from user={cq.from_user.id}")
        print(f"[📲 Gateway] Callback details: message_id={cq.message.message_id if cq.message else None}, chat_id={cq.message.chat.id if cq.message else None}")
        
        event = TgEvent(
            user_id=cq.from_user.id,
            chat_id=cq.message.chat.id if cq.message else cq.from_user.id,
            message_id=cq.message.message_id if cq.message else None,
            callback_data=cq.data,
            state=await state.get_state(),
            event_type="callback",
        )
        
        print(f"[📲 Gateway] Создан TgEvent: {event.model_dump()}")

        try:
            resp = await self._rpc.call(event)
            print(f"[📬 Gateway] RPC-ответ: {resp.model_dump()}")
        except asyncio.TimeoutError:
            await cq.answer("⚠️ Сервис не ответил", show_alert=True)
            return

        # Обрабатываем ответ
        if resp.action == "answer_callback":
            await cq.answer(resp.text or "")
        elif resp.action == "edit_message" and cq.message:
            await cq.message.edit_text(
                resp.text or "",
                reply_markup=self._renderer.render(resp.markup),
                parse_mode=resp.parse_mode,
            )
        elif resp.action == "send_message":
            await cq.message.answer(
                resp.text or "",
                reply_markup=self._renderer.render(resp.markup),
                parse_mode=resp.parse_mode,
            )


# ----------------------------------------------------------------------
# Удобная точка входа для скриптов
# ----------------------------------------------------------------------
async def _run(token: str, broker_url: str):
    gateway = AiogramGateway(token=token, broker_url=broker_url)
    await gateway.run()


def run_gateway(token: str, broker_url: str = "amqp://guest:guest@localhost/") -> None:  # noqa: D401
    """Синхронная оболочка для запуска бота."""
    asyncio.run(_run(token, broker_url)) 