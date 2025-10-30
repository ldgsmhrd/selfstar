from pydantic import BaseModel, Field
from typing import Optional


class CommentReplyRequest(BaseModel):
    # Context from the post/notification
    post_img: Optional[str] = None  # URL or data URI (optional, may be ignored by text model)
    post: Optional[str] = Field(None, description="Post caption text")
    personality: Optional[str] = Field(None, description="Persona tone/style text")
    text: str = Field(..., min_length=1, description="Incoming comment text to reply to")
    # Optional persona image if you want to bias tone visually (not used by base prompt)
    persona_img: Optional[str] = None


class CommentReplyResponse(BaseModel):
    ok: bool = True
    reply: str
