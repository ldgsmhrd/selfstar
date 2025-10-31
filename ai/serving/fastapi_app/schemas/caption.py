from pydantic import BaseModel, Field
from typing import Optional


class CaptionRequest(BaseModel):
    image: str = Field(..., min_length=10, description="Data URI or http(s) URL of the preview image")
    personality: Optional[str] = Field(None, description="Persona tone/style to reflect in the caption")
    tone: Optional[str] = Field(None, description="Optional tone hint, e.g., 'insta' | 'editorial' | 'playful'")


class CaptionResponse(BaseModel):
    ok: bool = True
    caption: str
