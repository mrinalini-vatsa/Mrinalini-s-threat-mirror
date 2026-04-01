from collections.abc import AsyncGenerator
import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()
database_url = os.getenv("DATABASE_URL", "")
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
if "sslmode=require" in database_url:
    database_url = database_url.replace("sslmode=require", "ssl=require")

engine = create_async_engine(
    database_url,
    echo=True,
    future=True,
    pool_pre_ping=True,
    connect_args={"ssl": "require"},
)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
SessionLocal = async_session


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
