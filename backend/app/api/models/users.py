"""
[파트 개요] 사용자 모델 접근 계층
- 내부 통신: aiomysql 풀을 이용해 사용자 조회/생성/업서트
- 외부 통신: 없음(직접 외부 API 호출 없음), DB 서버와의 통신만 수행
"""
# app/api/models/users.py
from __future__ import annotations
from typing import Optional, Dict, Any, Tuple
import aiomysql

from app.api.core.mysql import get_mysql_pool


# 내부 헬퍼: DictCursor 열기
async def _dict_cursor(conn) -> aiomysql.cursors.DictCursor:
    return conn.cursor(aiomysql.DictCursor)


# 단일 사용자 조회 (id 기준) — 항상 dict 또는 None 반환
async def find_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    pool = await get_mysql_pool()
    async with pool.acquire() as conn, await _dict_cursor(conn) as cur:
        await cur.execute(
            """
            SELECT user_id, user_platform, user_inherent, user_name,
                   user_nick, user_img, user_gender, user_phone, user_age,
                   user_birthday, user_language, user_credit, joined_at
            FROM ss_user
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,),
        )
        return await cur.fetchone()


# 사용자 조회 (inherent 단독 또는 platform+inherent)
async def find_user_by_inherent(
    user_inherent: str,
    provider: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    pool = await get_mysql_pool()
    async with pool.acquire() as conn, await _dict_cursor(conn) as cur:
        if provider:
            await cur.execute(
                """
                SELECT user_id, user_platform, user_inherent, user_name,
                       user_nick, user_img, user_gender, user_phone, user_age,
                       user_birthday, user_language, user_credit, joined_at
                FROM ss_user
                WHERE user_platform = %s AND user_inherent = %s
                LIMIT 1
                """,
                (provider, user_inherent),
            )
        else:
            await cur.execute(
                """
                SELECT user_id, user_platform, user_inherent, user_name,
                       user_nick, user_img, user_gender, user_phone, user_age,
                       user_birthday, user_language, user_credit, joined_at
                FROM ss_user
                WHERE user_inherent = %s
                LIMIT 1
                """,
                (user_inherent,),
            )
        return await cur.fetchone()


# 일반 회원 생성 — dict 반환
async def create_user(user: Dict[str, Any]) -> Dict[str, Any]:
    pool = await get_mysql_pool()
    async with pool.acquire() as conn, await _dict_cursor(conn) as cur:
        await cur.execute(
            """
            INSERT INTO ss_user
              (user_platform, user_inherent, user_name, user_nick, user_img,
               user_gender, user_phone, user_age, user_birthday, user_language, user_credit, joined_at)
            VALUES
              (%s, %s, %s, %s, %s,
               %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (
                user.get("user_platform"),
                user.get("user_inherent"),
                user.get("user_name"),
                user.get("user_nick"),
                user.get("user_img"),
                user.get("user_gender"),
                user.get("user_phone"),
                user.get("user_age"),
                user.get("user_birthday"),
                user.get("user_language"),
                user.get("user_credit", 100),
            ),
        )
        await conn.commit()
        user_id = cur.lastrowid
        return {**user, "user_id": user_id}


# OAuth upsert — 항상 dict 반환, 여분 키워드(db 등)는 무시
async def upsert_user_from_oauth(
    provider: str,
    inherent: str,
    nick: Optional[str] = None,
    img: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    if not provider or not inherent:
        raise ValueError("provider/inherent 누락")

    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        # 1) 기존 존재 여부 확인 (간단한 구분용)
        existed = False
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """
                SELECT user_id FROM ss_user
                WHERE user_platform = %s AND user_inherent = %s
                LIMIT 1
                """,
                (provider, inherent),
            )
            existed = await cur.fetchone() is not None

        # 2) upsert (중복키 전제: user_inherent 또는 (user_platform, user_inherent) UNIQUE)
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO ss_user
                  (user_platform, user_inherent, user_nick, user_img, user_credit)
                VALUES
                  (%s, %s, %s, %s, 100)
                ON DUPLICATE KEY UPDATE
                  user_platform = VALUES(user_platform),
                  user_nick     = COALESCE(VALUES(user_nick), user_nick),
                  user_img      = COALESCE(VALUES(user_img),  user_img)
                """,
                (provider, inherent, nick, img),
            )
            await conn.commit()

        # 3) 조회는 DictCursor로
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """
                SELECT user_id, user_platform, user_inherent, user_name,
                       user_nick, user_img, user_gender, user_phone, user_age,
                       user_birthday, user_language, user_credit, joined_at
                FROM ss_user
                WHERE user_platform = %s AND user_inherent = %s
                LIMIT 1
                """,
                (provider, inherent),
            )
            row = await cur.fetchone()
            if not row:
                raise RuntimeError("upsert 이후 사용자 조회 실패")
            # is_new 플래그 첨부 (기존에 없던 사용자면 True)
            row["is_new"] = not existed
            return row
