# shared/schemas.py
from pydantic import BaseModel
from typing import Optional, Literal, Dict, Any

class TgEvent(BaseModel):
    user_id: int
    chat_id: int
    message_id: Optional[int]
    text: Optional[str]
    callback_data: Optional[str]
    state: Optional[str]
    event_type: Literal["message", "callback", "command"]
    metadata: Optional[Dict[str, Any]] = {}

class TgResponse(BaseModel):
    action: Literal["send_message", "edit_message", "answer_callback", "none"]
    text: Optional[str] = None
    next_state: Optional[str] = None
    markup: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
