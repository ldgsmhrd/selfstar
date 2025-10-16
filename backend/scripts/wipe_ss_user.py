import asyncio
import aiomysql
import os

# Uses the same env vars as the app (DB_HOST, DB_USER, DB_PASS, DB_NAME, DB_PORT)

async def run():
    host = os.getenv("DB_HOST", "project-db-cgi.smhrd.com")
    user = os.getenv("DB_USER", "cgi_25IS_LI1_p3_3")
    password = os.getenv("DB_PASS", "smhrd3")
    db = os.getenv("DB_NAME", "cgi_25IS_LI1_p3_3")
    port = int(os.getenv("DB_PORT", 3307))

    pool = await aiomysql.create_pool(host=host, user=user, password=password, db=db, port=port, autocommit=True)
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # Count before
            await cur.execute("SELECT COUNT(*) AS cnt FROM ss_user")
            before = (await cur.fetchone())["cnt"]
            print(f"[wipe] ss_user rows before: {before}")

            try:
                # Try FK-safe truncate in a single connection scope
                await cur.execute("SET FOREIGN_KEY_CHECKS=0")
                await cur.execute("TRUNCATE TABLE ss_user")
                await cur.execute("SET FOREIGN_KEY_CHECKS=1")
            except Exception as e:
                print(f"[wipe] TRUNCATE failed: {e}. Falling back to DELETE ...")
                await cur.execute("DELETE FROM ss_user")

            # Count after
            await cur.execute("SELECT COUNT(*) AS cnt FROM ss_user")
            after = (await cur.fetchone())["cnt"]
            print(f"[wipe] ss_user rows after: {after}")

    pool.close()
    await pool.wait_closed()


if __name__ == "__main__":
    asyncio.run(run())
