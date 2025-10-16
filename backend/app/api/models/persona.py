"""
[파트 개요] persona 모델 액세스
- 내부 통신: aiomysql 풀을 이용해 ss_persona 테이블에 INSERT
"""
from __future__ import annotations
import aiomysql
import json
from typing import Any, Dict
from app.api.core.mysql import get_mysql_pool


async def _dict_cursor(conn) -> aiomysql.cursors.DictCursor:
    return conn.cursor(aiomysql.DictCursor)


async def create_persona(
    user_id: int,
    persona_img: str,
    persona_parameters: Dict[str, Any],
) -> int:
    """
    ss_persona에 새 레코드를 추가하고 생성된 PK를 반환합니다.
    """
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # JSON 직렬화 보장: 문자열로 변환 후 CAST AS JSON
            sql = (
                "INSERT INTO ss_persona (user_id, persona_img, persona_parameters) "
                "VALUES (%s, %s, CAST(%s AS JSON))"
            )
            await cur.execute(
                sql,
                (
                    user_id,
                    persona_img,
                    json.dumps(persona_parameters, ensure_ascii=False),
                ),
            )
            return cur.lastrowid or 0
