from __future__ import annotations
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import aiomysql

from app.api.core.mysql import get_mysql_pool
from .oauth_instagram import _require_login


router = APIRouter(prefix="/api/instagram", tags=["instagram"]) 


class AckBody(BaseModel):
    ids: List[str]
    persona_num: Optional[int] = None  # 선택 정보(로깅용), 필터링에는 사용 안함


@router.post("/notifications/ack")
async def acknowledge_notifications(request: Request, body: AckBody):
    """클라이언트가 확인(읽음 처리)한 알림 ID들을 서버에 기록.

    - 저장 테이블: ss_instagram_event_seen (미존재 시 무시하고 성공 처리)
    - 외부 ID는 Graph의 comment ID(예: 179xxxx) 등 고유 식별자 사용
    - 중복은 무시(UNIQUE 제약 조건 가정)
    """
    user_id = _require_login(request)
    ids = [i for i in (body.ids or []) if isinstance(i, str) and i]
    if not ids:
        return {"ok": True, "acknowledged": 0}

    inserted = 0
    try:
        pool = await get_mysql_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                for eid in ids:
                    try:
                        # user_id, persona 정보는 부가정보로만 저장(필터링은 external_id 기준)
                        await cur.execute(
                            """
                            INSERT INTO ss_instagram_event_seen (external_id, user_id, user_persona_num)
                            VALUES (%s, %s, %s)
                            ON DUPLICATE KEY UPDATE updated_at=CURRENT_TIMESTAMP
                            """,
                            (str(eid), int(user_id), int(body.persona_num) if body.persona_num is not None else None),
                        )
                        inserted += 1
                    except Exception:
                        # 테이블 미존재 또는 UNIQUE 충돌 시 건너뜀
                        pass
                try:
                    await conn.commit()
                except Exception:
                    pass
    except Exception:
        # 커넥션 오류/테이블 미존재 시에도 API는 성공으로 간주
        return {"ok": True, "acknowledged": 0}

    return {"ok": True, "acknowledged": inserted}
