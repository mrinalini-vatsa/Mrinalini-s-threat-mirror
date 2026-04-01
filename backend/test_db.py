import asyncio
import os

import asyncpg
from dotenv import load_dotenv


async def main() -> None:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL", "")
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if "sslmode=require" in database_url:
        database_url = database_url.replace("sslmode=require", "ssl=require")
    try:
        conn = await asyncpg.connect(database_url, ssl="require")
        try:
            await conn.execute("SELECT 1;")
        finally:
            await conn.close()
        print("✅ Connected to Neon DB!")
    except Exception as exc:
        print(f"DB connection failed: {exc!r}")


if __name__ == "__main__":
    asyncio.run(main())
