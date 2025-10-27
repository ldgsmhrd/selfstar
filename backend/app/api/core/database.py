"""
[파트 개요] DB 세션/엔진 설정
- 내부 통신: SQLAlchemy AsyncEngine/Session을 통해 MySQL 접속 관리
- 외부 통신: 실제 DB 서버(project-db-cgi.smhrd.com:3307)와의 연결 파라미터 구성
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.api.core.db import get_mysql_pool

DB_HOST = os.getenv("DB_HOST", "project-db-cgi.smhrd.com")
DB_PORT = os.getenv("DB_PORT", "3307")
DB_USER = os.getenv("DB_USER", "cgi_25IS_LI1_p3_3")
DB_PASS = os.getenv("DB_PASS", "smhrd3")
DB_NAME = os.getenv("DB_NAME", "cgi_25IS_LI1_p3_3")

DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
