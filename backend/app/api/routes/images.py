"""이미지 API 라우트: AI 미리보기, 오브젝트 스토리지(S3) 저장, 프리사인 URL 재발급"""
from fastapi import APIRouter, HTTPException, Request
import os
import httpx
import logging
import re

from app.api.schemas.images import (
    GenerateImageRequest,
    ImageSaveRequest,
    ImageUrlRequest,
)
from app.core.s3 import s3_enabled, put_data_uri, presign_get_url
from app.api.models.persona import update_persona_img

router = APIRouter(prefix="/api", tags=["images"])
log = logging.getLogger("images")




@router.post("/images/preview", summary="AI 미리보기(저장 없음)")
async def preview_image(payload: GenerateImageRequest):
    ai_url = (os.getenv("AI_SERVICE_URL") or "http://localhost:8600").rstrip("/")
    body = payload.model_dump(exclude_none=True)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{ai_url}/predict", json=body)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ai_delegate_error: {e}")

    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="ai_failed")
    data = r.json()
    image = data.get("image")
    if not (isinstance(image, str) and image.startswith("data:")):
        raise HTTPException(status_code=502, detail="invalid_ai_response")
    return {"ok": True, "image": image}


@router.post("/images/save", summary="미리보기 데이터 저장")
async def save_image(body: ImageSaveRequest, request: Request):
    """미리보기 이미지를 저장합니다.

    동작:
    - S3(오브젝트 스토리지) 설정이 필수입니다.
    - 업로드 후 {key, url(프리사인)}을 반환합니다.
    """
    try:
    # 세션에서 사용자 확인 (DB 기록 및 권한 확인용)
        user_id = request.session.get("user_id")
        if not user_id:
            # 로컬 검증 전용(개발 모드): DEV_ALLOW_DEBUG_USER=1일 때 X-Debug-User-Id 헤더 허용
            if os.getenv("DEV_ALLOW_DEBUG_USER", "0") in ("1", "true", "yes"):
                try:
                    debug_uid = request.headers.get("X-Debug-User-Id")
                    if debug_uid and debug_uid.isdigit():
                        user_id = int(debug_uid)
                except Exception:
                    pass
        if not user_id:
            raise HTTPException(status_code=401, detail="not_authenticated")



        if not s3_enabled():
            raise HTTPException(status_code=400, detail="s3_not_configured")

        key = put_data_uri(
            body.image,
            model=body.model,
            key_prefix=body.prefix,
            base_prefix=(body.base_prefix if body.base_prefix is not None else None),
            include_model=bool(body.include_model) if body.include_model is not None else True,
            include_date=bool(body.include_date) if body.include_date is not None else True,
        )
        url = presign_get_url(key)
    # 선택: body.persona_num 이 있으면 ss_persona.persona_img 에 즉시 저장
        if body.persona_num:
            try:
                await update_persona_img(int(user_id), int(body.persona_num), key)
            except Exception as _e:
                log.warning("failed to update persona_img: %s", _e)
        return {"ok": True, "key": key, "url": url}
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_data_uri")
    except HTTPException:
        raise
    except Exception as e:
        log.warning("failed to save image: %s", e)
        raise HTTPException(status_code=500, detail="save_failed")


    


@router.post("/images/url", summary="S3 오브젝트 URL 재발급(프리사인)")
async def renew_image_url(req: ImageUrlRequest):
    """기존 오브젝트 키에 대한 프리사인 GET URL을 재발급합니다.

    S3 설정이 필요하며, 미설정 시 400을 반환합니다.
    """
    try:
        if not s3_enabled():
            raise HTTPException(status_code=400, detail="s3_not_configured")
        url = presign_get_url(req.key)
        return {"ok": True, "key": req.key, "url": url}
    except HTTPException:
        raise
    except Exception as e:
        log.warning("failed to presign url for %s: %s", req.key, e)
        raise HTTPException(status_code=500, detail="presign_failed")
