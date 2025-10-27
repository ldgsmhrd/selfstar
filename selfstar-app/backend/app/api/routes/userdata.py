# -*- coding: utf-8 -*-
"""
[파트 개요] 유저 정보 데이터 라우터
- 프론트 통신: 세션 사용자 정보 일부 업데이트(생년월일/성별)
- 외부 통신: 없음

Endpoint
- PUT /api/users/me/profile: 세션 사용자의 성별+생년월일 동시 저장
"""
from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from app.api.models.users import find_user_by_id, update_user_profile
from app.api.schemas.user import ProfilePayload

# 프런트가 호출하는 경로(/api/users/...)에 맞춰 prefix를 /api로 지정
router = APIRouter(prefix="/api/users", tags=["users"])


@router.put("/me/profile", summary="내 프로필 업데이트(생일, 성별)")
async def put_my_profile(payload: ProfilePayload, request: Request):
    # 세션에서 로그인 사용자 확인
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not logged in")

    # 세션의 사용자 유효성 확인
    user = await find_user_by_id(int(user_id))
    if not user:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Session user not found")

    # DB 업데이트
    updated = await update_user_profile(int(user_id), payload.birthday, payload.gender)

    return JSONResponse(
        {
            "ok": True,
            "user": {
                "id": updated["user_id"],
                "birthday": str(updated.get("user_birthday"))
                if updated.get("user_birthday")
                else None,
                "gender": updated.get("user_gender"),
            },
        }
    )
