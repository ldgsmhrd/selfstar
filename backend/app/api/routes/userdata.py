# -*- coding: utf-8 -*-
"""
[파트 개요] 유저 정보 데이터 라우터
- 프론트 통신: 세션 사용자 정보 일부 업데이트(생년월일)
- 외부 통신: 없음

Endpoint
- PATCH /user/me/birthday: 세션 사용자의 생년월일(YYYY-MM-DD) 저장
"""
from __future__ import annotations
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from datetime import date

from app.api.models.users import update_user_birthday, find_user_by_id, update_user_profile

router = APIRouter()

class BirthdayPayload(BaseModel):
    birthday: date

    @field_validator("birthday")
    @classmethod
    def validate_birthday(cls, v: date):
        # 미래 날짜 방지 (오늘 이후 불허)
        if v > date.today():
            raise ValueError("미래 날짜는 허용되지 않습니다.")
        # 합리적인 최소 연도 제한(1900)
        if v.year < 1900:
            raise ValueError("유효하지 않은 생년월일입니다.")
        return v

@router.patch("/user/me/birthday")
async def patch_my_birthday(payload: BirthdayPayload, request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not logged in")

    # 존재 여부 확인(선택)
    user = await find_user_by_id(int(user_id))
    if not user:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Session user not found")

    updated = await update_user_birthday(int(user_id), payload.birthday)
    return JSONResponse({
        "ok": True,
        "user": {
            "id": updated["user_id"],
            "birthday": str(updated.get("user_birthday")) if updated.get("user_birthday") else None,
        }
    })


class ProfilePayload(BaseModel):
    birthday: date
    gender: str

    @field_validator("birthday")
    @classmethod
    def validate_birthday(cls, v: date):
        if v > date.today():
            raise ValueError("미래 날짜는 허용되지 않습니다.")
        if v.year < 1900:
            raise ValueError("유효하지 않은 생년월일입니다.")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str):
        allowed = {"남성", "여성"}
        if v not in allowed:
            raise ValueError("성별은 남성/여성 중 하나여야 합니다.")
        return v


@router.patch("/user/me/profile")
async def patch_my_profile(payload: ProfilePayload, request: Request):
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
