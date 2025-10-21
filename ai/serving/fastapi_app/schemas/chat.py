from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    persona_img: Optional[str] = None
    messages: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    ok: bool = True
    reply: str