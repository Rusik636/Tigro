import pytest

from tigro.core import Router, Context
from tigro.contracts import Handler
from typing import cast
from tigro.matchers import Command
from shared.schemas import TgEvent, TgResponse


class DummyPublisher:
    def __init__(self) -> None:
        self.sent: list[TgResponse] = []

    async def publish(self, user_id: int, resp: TgResponse) -> None:
        self.sent.append(resp)
        return None


@pytest.mark.asyncio
async def test_basic_dispatch() -> None:
    pub = DummyPublisher()
    router = Router(publisher=pub)

    async def handler(ctx: Context) -> None:
        await ctx.send_message("ok")
        return None

    router.register(Command("/ping"), cast(Handler, handler))

    event = TgEvent(
        user_id=1,
        chat_id=1,
        message_id=1,
        text="/ping",
        callback_data=None,
        state=None,
        event_type="message",
    )
    await router.dispatch(event)
    assert pub.sent[0].text == "ok"
