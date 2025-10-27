from pydantic import BaseModel, Field
from typing import List, Optional


class GenerateImageRequest(BaseModel):
    """Frontend image generation request payload.

    Kept 1:1 with the client shape and minimal validation; the route will
    forward this body to the AI service as-is (excluding None fields).
    """

    name: str = Field(..., min_length=1, max_length=100)
    gender: str = Field(..., min_length=1, max_length=10)
    age: Optional[int] = None
    options: List[str] = Field(default_factory=list)

    faceShape: Optional[str] = None
    skinTone: Optional[str] = None
    hair: Optional[str] = None
    eyes: Optional[str] = None
    nose: Optional[str] = None
    lips: Optional[str] = None

    bodyType: Optional[str] = None
    glasses: Optional[str] = None
    personalities: Optional[List[str]] = None


class ImageSaveRequest(BaseModel):
    """Payload for saving a preview data URI to disk."""
    image: str = Field(..., description="data:image/*;base64,... data URI")
