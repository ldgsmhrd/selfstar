from pydantic import BaseModel, Field
from typing import List, Optional


class PredictRequest(BaseModel):
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

    # 하위호환 필드
    feature: Optional[str] = Field(None, max_length=2000)
    featureCombined: Optional[str] = Field(None, max_length=2000)
