# tigro/schemas.py
"""Pydantic-схемы событий и ответов Telegram."""

from pydantic import BaseModel
from typing import Optional, Literal, Dict, Any

class TgEvent(BaseModel):
    user_id: int
    chat_id: int
    message_id: Optional[int] = None
    text: Optional[str] = None
    callback_data: Optional[str] = None
    state: Optional[str] = None
    event_type: Literal["message", "callback", "command"]
    metadata: Optional[Dict[str, Any]] = {}
    correlation_id: Optional[str] = None

class TgResponse(BaseModel):
    action: Literal["send_message", "edit_message", "answer_callback", "none"]
    text: Optional[str] = None
    next_state: Optional[str] = None
    markup: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    correlation_id: Optional[str] = None
    parse_mode: Optional[str] = None 