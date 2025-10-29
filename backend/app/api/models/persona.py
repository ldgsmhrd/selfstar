"""
[파트 개요] persona 모델 액세스
- 내부 통신: aiomysql 풀을 이용해 ss_persona 테이블에 INSERT
"""
from __future__ import annotations
import aiomysql
import json
from typing import Any, Dict, List
from app.api.core.mysql import get_mysql_pool
import logging

log = logging.getLogger("personas")


async def _dict_cursor(conn) -> aiomysql.cursors.DictCursor:
    return conn.cursor(aiomysql.DictCursor)


async def create_persona(
    user_id: int,
    persona_img: str,
    persona_parameters: Dict[str, Any],
) -> tuple[int, int]:
    """
    ss_persona에 새 레코드를 추가하고 생성된 PK를 반환합니다.
    """
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # 현재 보유 개수 및 최대 user_persona_num 확인
            await cur.execute(
                """
                SELECT COUNT(*) AS cnt, COALESCE(MAX(user_persona_num), 0) AS mx
                FROM ss_persona
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = await cur.fetchone() or {"cnt": 0, "mx": 0}
            if int(row["cnt"]) >= 4:
                raise ValueError("persona_limit_reached")
            next_num = int(row["mx"]) + 1
            log.info("persona count=%s next_num=%s for user_id=%s", row.get("cnt"), next_num, user_id)

        async with conn.cursor() as cur:
            # JSON 직렬화 보장: 문자열로 변환하여 저장 (DB 컬럼 타입이 JSON이든 TEXT이든 호환)
            sql = (
                "INSERT INTO ss_persona (user_id, user_persona_num, persona_img, persona_parameters) "
                "VALUES (%s, %s, %s, %s)"
            )
            params_json = json.dumps(persona_parameters, ensure_ascii=False)
            await cur.execute(sql, (user_id, next_num, persona_img, params_json))
            try:
                await conn.commit()
            except Exception:
                # pool autocommit may be enabled; ignore commit error
                pass
            rid = cur.lastrowid or 0
            log.info("persona inserted id=%s for user_id=%s num=%s", rid, user_id, next_num)
            return rid, next_num
    
async def get_user_personas(user_id: int) -> List[Dict[str, Any]]:
    """
    사용자 ID에 대한 모든 페르소나를 반환합니다.
    """
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """
                SELECT user_persona_num, persona_img, persona_parameters
                FROM ss_persona
                WHERE user_id = %s
                ORDER BY user_persona_num
                """,
                (user_id,),
            )
            personas = await cur.fetchall()
            for persona in personas:
                persona['persona_parameters'] = json.loads(persona['persona_parameters'])
            return personas


async def update_persona_img(user_id: int, persona_num: int, img_value: str) -> None:
    """Update persona_img for the given user and persona number.

    img_value should be an S3 key when using Object Storage, or a /media/... URL when using local storage.
    """
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE ss_persona
                SET persona_img = %s
                WHERE user_id = %s AND user_persona_num = %s
                LIMIT 1
                """,
                (img_value, user_id, persona_num),
            )
            try:
                await conn.commit()
            except Exception:
                pass
