# -*- coding: utf-8 -*-
"""
[파트 개요] 유저 정보 데이터 라우터
- 프론트 통신: 세션 사용자 정보 일부 업데이트(생년월일)
- 외부 통신: 없음

Endpoint
- PUT /users/me/profile: 세션 사용자의 성별+생년월일 동시 저장
"""
from __future__ import annotations
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import date

from app.api.models.users import find_user_by_id, update_user_profile
from app.api.schemas.user import ProfilePayload

router = APIRouter(prefix="/users", tags=["users"])

@router.put("/me/profile")
async def put_my_profile(payload: ProfilePayload, request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not logged in")

    user = await find_user_by_id(int(user_id))
    if not user:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Session user not found")

    updated = await update_user_profile(int(user_id), payload.birthday, payload.gender)
    return JSONResponse({
        "ok": True,
        "user": {
            "id": updated["user_id"],
            "birthday": str(updated.get("user_birthday")) if updated.get("user_birthday") else None,
            "gender": updated.get("user_gender"),
        }
    })
