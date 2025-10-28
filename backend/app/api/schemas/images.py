from pydantic import BaseModel, Field
from typing import List, Optional


class GenerateImageRequest(BaseModel):
    """프론트엔드 이미지 생성 요청 페이로드.

    클라이언트 구조를 그대로 유지하며 최소한의 검증만 수행합니다.
    None 값은 제외하여 AI 서비스로 그대로 전달됩니다.
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
    """미리보기 data URI를 저장하기 위한 페이로드"""
    image: str = Field(..., description="data:image/*;base64,... 형태의 data URI")
    model: Optional[str] = Field(
        default=None,
        description="S3 키 경로에 포함할 선택적 모델 식별자 (예: 'gemini', 'sdxl')",
    )
    prefix: Optional[str] = Field(
        default=None,
        description="기본 prefix 하위의 선택적 서브폴더 (예: 'personas/123'). 선행 슬래시 금지",
        min_length=1,
        max_length=200,
    )
    base_prefix: Optional[str] = Field(
        default=None,
        description="기본 prefix 재정의 (기본: NCP_S3_PREFIX). 빈 문자열이면 기본 prefix 비활성화",
        max_length=100,
    )
    include_model: Optional[bool] = Field(
        default=True,
        description="키 경로에 모델 세그먼트를 포함할지 여부 (기본: true)",
    )
    include_date: Optional[bool] = Field(
        default=True,
        description="키 경로에 YYYYMMDD 날짜 세그먼트를 포함할지 여부 (기본: true)",
    )
    persona_num: Optional[int] = Field(
        default=None,
        description="지정 시 현재 사용자/해당 번호의 ss_persona.persona_img 에 저장된 키/URL을 반영",
        ge=1,
        le=9999,
    )


class ImageUrlRequest(BaseModel):
    """기존 오브젝트 키에 대한 프리사인 GET URL 재발급 요청"""
    key: str = Field(..., min_length=3, description="버킷 내부 오브젝트 키")
