import asyncio
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

load_dotenv()

from app.api.routes import router
from app.core.database import Base, engine
from app.core.logging import setup_logging
from app.workers.alert_worker import run_alert_worker

setup_logging()
logger = logging.getLogger(__name__)

stop_event = asyncio.Event()
worker_task: asyncio.Task | None = None


app = FastAPI(title="Mrinalini ThreatMirror API")


@app.on_event("startup")
async def create_tables() -> None:
    try:
        # Auto-create tables for local/dev usage without requiring Alembic.
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema verified/created")
    except Exception:
        # Keep API up even if DB is temporarily unavailable.
        logger.exception("Database initialization failed")


@app.on_event("startup")
async def start_worker() -> None:
    global worker_task
    stop_event.clear()
    worker_task = asyncio.create_task(run_alert_worker(stop_event))


@app.on_event("shutdown")
async def stop_worker() -> None:
    stop_event.set()
    if worker_task:
        await worker_task
    logger.info("API shutdown complete")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok", "db": "connected"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8001))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
