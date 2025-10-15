from typing import List, Optional
import re
import os
import base64
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import logging

# 시그니처: generate_image(name, gender, feature, options) -> bytes (PNG)
# 환경변수 GOOGLE_API_KEY 필요
# 모델: gemini-2.5-flash-image-preview (이미지 생성)

MODEL_NAME = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image-preview")

_client = None
log = logging.getLogger("gemini")

# Load repo root .env to pick up GOOGLE_API_KEY reliably
_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
_ENV_PATH = os.path.join(_REPO_ROOT, ".env")
try:
    load_dotenv(dotenv_path=_ENV_PATH, override=True)
    log.info(f"[gemini] loaded .env from {_ENV_PATH}")
except Exception as _e:
    log.warning(f"[gemini] failed to load .env: {_e}")

def _get_client():
    global _client
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
    if _client is None:
        _client = genai.Client(api_key=api_key)
    return _client


def _parse_details(feature_text: str) -> dict:
    """프론트/백엔드에서 조합해 온 feature 문자열에서 라벨별 값을 파싱합니다.
    예: "얼굴형:계란형, 피부톤:밝은 17~21호, 헤어:스트레이트, 눈:크고 또렷함, 코:오똑함, 입:도톰 | 성격:활발함/지적인"
    """
    d = {
        "faceShape": None,
        "skinTone": None,
        "hair": None,
        "eyes": None,
        "nose": None,
        "lips": None,
        "personalities": None,
        "extra": None,
    }
    text = feature_text or ""
    # 파트별로 분리 ( | 와 , 를 모두 구분자로 사용 )
    parts = re.split(r"\s*[|]\s*|\s*,\s*", text)
    rest: List[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # 라벨 매칭
        if p.startswith("얼굴형:"):
            d["faceShape"] = p.split(":", 1)[1].strip()
        elif p.startswith("피부톤:"):
            d["skinTone"] = p.split(":", 1)[1].strip()
        elif p.startswith("헤어:"):
            d["hair"] = p.split(":", 1)[1].strip()
        elif p.startswith("눈:"):
            d["eyes"] = p.split(":", 1)[1].strip()
        elif p.startswith("코:"):
            d["nose"] = p.split(":", 1)[1].strip()
        elif p.startswith("입:"):
            d["lips"] = p.split(":", 1)[1].strip()
        elif p.startswith("성격:"):
            val = p.split(":", 1)[1].strip()
            d["personalities"] = [v.strip() for v in re.split(r"[\/|,]", val) if v.strip()]
        else:
            rest.append(p)
    if rest:
        d["extra"] = ", ".join(rest)
    return d


def _build_prompt(name: str, gender: str, feature: Optional[str], options: List[str]) -> str:
    # 이전 동작에 가깝게: 단순 텍스트 설명을 그대로 전달 + 최소 가이드만 추가
    desc = feature or ""
    base = f"Create a single photorealistic, front-facing portrait of a {gender}."
    if name:
        base = f"{base} The person is named '{name}'."
    guidance = (
        "Natural lighting, shallow depth of field, realistic skin texture. "
        "Plain light gray studio background and a simple white t-shirt. "
        "Output as high-quality PNG."
    )
    # feature 문자열이 있으면 그대로 뒤에 추가하여 사용자 설명을 보존
    full = f"{base} {guidance} Details: {desc}" if desc else f"{base} {guidance}"
    return full


def generate_image(name: str, gender: str, feature: Optional[str], options: List[str]):
    client = _get_client()
    prompt = _build_prompt(name, gender, feature, options)
    log.info(f"[gemini] prompt: {prompt[:300]}{'...' if len(prompt)>300 else ''}")

    # Note: google-genai's Part.from_text is keyword-only. Passing a raw string can
    # trigger an internal call like Part.from_text(prompt) (positional), which breaks on
    # some versions with: "Part.from_text() takes 1 positional argument but 2 were given".
    # To avoid that, explicitly build Parts with keyword args and pass a list.
    image_response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[types.Part.from_text(text=prompt)],
        config=types.GenerateContentConfig(
            response_modalities=[types.Modality.IMAGE],
            candidate_count=1,
        ),
    )

    # 응답에서 이미지 후보를 찾아 바이트와 mime을 반환
    # 우선 inline_data가 있는 파트를 순회하며, mime_type을 함께 사용
    try:
        def sniff_mime(buf: bytes) -> str:
            if buf.startswith(b"\x89PNG\r\n\x1a\n"):
                return "image/png"
            if buf.startswith(b"\xff\xd8\xff"):
                return "image/jpeg"
            if len(buf) >= 12 and buf[:4] == b"RIFF" and buf[8:12] == b"WEBP":
                return "image/webp"
            return "application/octet-stream"

        for cand in getattr(image_response, "candidates", []) or []:
            parts = getattr(cand.content, "parts", []) or []
            for part in parts:
                inline = getattr(part, "inline_data", None)
                if inline and getattr(inline, "data", None) is not None:
                    raw = inline.data
                    if isinstance(raw, (bytes, bytearray)):
                        out = bytes(raw)
                    elif isinstance(raw, str):
                        out = base64.b64decode(raw)
                    else:
                        # Unknown type; try to coerce via bytes()
                        try:
                            out = bytes(raw)
                        except Exception:
                            raise RuntimeError(f"unexpected inline_data.data type: {type(raw)}")
                    mime = getattr(inline, "mime_type", None) or sniff_mime(out)
                    log.info(f"[gemini] decoded image bytes: {len(out)} bytes, mime: {mime}")
                    return out, mime
                # 일부 버전에서 part.data로 제공될 수 있음
                if hasattr(part, "data") and part.data:
                    raw = part.data
                    if isinstance(raw, (bytes, bytearray)):
                        out = bytes(raw)
                    elif isinstance(raw, str):
                        out = base64.b64decode(raw)
                    else:
                        try:
                            out = bytes(raw)
                        except Exception:
                            raise RuntimeError(f"unexpected part.data type: {type(raw)}")
                    mime = sniff_mime(out)
                    log.info(f"[gemini] decoded image bytes: {len(out)} bytes (part.data), mime: {mime}")
                    return out, mime
        raise RuntimeError("응답에서 이미지 데이터를 찾지 못했습니다.")
    except Exception as e:
        raise RuntimeError(f"Gemini 이미지 응답 파싱 실패: {e}")
