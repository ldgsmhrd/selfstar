from fastapi import APIRouter, HTTPException
import logging
import os
from typing import List

from google import genai
from google.genai import types

from ai.serving.fastapi_app.schemas.comment import CommentReplyRequest, CommentReplyResponse

router = APIRouter()
log = logging.getLogger("ai-comment")

_client = None


def _get_client():
    global _client
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
    if _client is None:
        _client = genai.Client(api_key=api_key)
    return _client


GEMINI_TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-flash")


def _build_comment_reply_prompt(req: CommentReplyRequest) -> str:
    # Derived from ai/notebooks/comment_model.ipynb (Korean prompt),
    # with small safety/format clarifications and output-only requirement.
    post_img = req.post_img or ""
    post = req.post or ""
    personality = req.personality or ""
    text = req.text or ""

    return f"""
당신은 유명한 인플루언서처럼 대화하는 엔지니어입니다.
다음 원칙을 지켜 댓글 답변을 생성하세요:
- 존댓말만 사용합니다.
- 문맥과 의도에 맞는 자연스러운 답변을 제공합니다.
- 입력받은 personality의 말투를 반영합니다.
- 이모티콘은 사용하지 않습니다.
- 최종 출력은 답변 문장만 출력합니다. 접두사/접미사/형식 텍스트를 추가하지 마세요.
- 최대 길이는 30 토큰 정도로 간결하게 마무리합니다.

예시 )
post_img="한강 사진"
post = "한강에 바람쐬러 나왔어요!"
personality = "활기찬"
text =  "오늘 날씨가 너무 좋아서 산책 나가셨나 보네요!"
output = "네! 이런 날엔 산책하며 힐링하는 게 정말 좋아요!"

아래 입력을 바탕으로 output 값만 출력하세요.
post_img="{post_img}"
post="{post}"
personality="{personality}"
text="{text}"
output = """"".strip()


@router.post("/comment/reply", response_model=CommentReplyResponse)
async def generate_comment_reply(req: CommentReplyRequest):
    try:
        client = _get_client()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"model_unavailable: {e}")

    prompt = _build_comment_reply_prompt(req)

    try:
        resp = client.models.generate_content(
            model=GEMINI_TEXT_MODEL,
            contents=[types.Part.from_text(text=prompt)],
            config=types.GenerateContentConfig(
                response_modalities=[types.Modality.TEXT],
                candidate_count=1,
                temperature=0.4,
                top_p=0.9,
                max_output_tokens=64,
            ),
        )
        reply = ""
        for c in getattr(resp, "candidates", []) or []:
            for p in getattr(c.content, "parts", []) or []:
                if getattr(p, "text", None):
                    reply += p.text
        reply = (reply or "").strip()
        if not reply:
            raise RuntimeError("empty_reply")
        # Post-process: ensure we didn't leak format markers
        if reply.lower().startswith("output"):
            # Try to strip patterns like: output = "..."
            idx = reply.find("=")
            if idx != -1:
                reply = reply[idx+1:].strip().strip('"')
        return CommentReplyResponse(ok=True, reply=reply)
    except HTTPException:
        raise
    except Exception as e:
        log.error("/comment/reply failed: %s", e)
        raise HTTPException(status_code=500, detail={"error": "comment_reply_failed", "message": str(e)})
