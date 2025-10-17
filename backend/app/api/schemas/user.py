from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date

class UserBase(BaseModel):
    user_platform: str
    user_inherent: str
    user_nick: Optional[str] = None
    user_img: Optional[str] = None
    user_credit: Optional[str] = "standard"

class UserCreate(UserBase):
    password: Optional[str] = None

class UserOut(UserBase):
    user_id: int
    password: Optional[str] = None

    class Config:
        from_attributes = True


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
