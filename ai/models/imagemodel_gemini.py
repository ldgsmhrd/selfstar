from typing import List, Optional
import os
import base64
from google import genai
from google.genai import types

# 시그니처: generate_image(name, gender, feature, options) -> bytes (PNG)
# 환경변수 GOOGLE_API_KEY 필요
# 모델: gemini-2.5-flash-image-preview (이미지 생성)

MODEL_NAME = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image-preview")

_client = None

def _get_client():
    global _client
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
    if _client is None:
        _client = genai.Client(api_key=api_key)
    return _client


def _build_prompt(name: str, gender: str, feature: Optional[str], options: List[str]) -> str:
    # 노트북의 사용자 입력 구성 로직을 반영
    user_input = {
        "이름": name,
        "성별": gender,
        "특징": feature or "",
        "옵션": ", ".join(options) if options else "",
    }
    user_input_str = ", ".join([f"{k} {v}" for k, v in user_input.items() if v])

    prompt_request = (
        f"{user_input_str}. "
        "Very high resolution, ultra-realistic, photorealistic front-facing portrait, "
        "clean, plain light grey background, wearing a plain white t-shirt."
    )
    return prompt_request


def generate_image(name: str, gender: str, feature: Optional[str], options: List[str]) -> bytes:
    client = _get_client()
    prompt = _build_prompt(name, gender, feature, options)

    image_response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_modalities=[types.Modality.IMAGE],
            candidate_count=1,
        ),
    )

    # 응답에서 첫 번째 이미지 후보를 PNG 바이트로 변환
    # google-genai 클라이언트의 이미지 응답 형식에 맞추어 디코딩
    # 보통 image_response.candidates[0].content.parts[0].inline_data.data (base64) 형태
    try:
        candidate = image_response.candidates[0]
        part = candidate.content.parts[0]
        # inline_data 또는 image_bytes 속성 등 형태에 따라 처리
        if hasattr(part, "inline_data") and getattr(part.inline_data, "data", None):
            data_b64 = part.inline_data.data
            return base64.b64decode(data_b64)
        elif hasattr(part, "data") and part.data:
            return base64.b64decode(part.data)
        else:
            raise RuntimeError("응답에서 이미지 데이터(part.inline_data.data)를 찾지 못했습니다.")
    except Exception as e:
        raise RuntimeError(f"Gemini 이미지 응답 파싱 실패: {e}")
