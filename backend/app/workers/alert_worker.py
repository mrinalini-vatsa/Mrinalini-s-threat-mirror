import asyncio
import logging

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.alert_pipeline import generate_random_alert, process_alert

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_alert_worker(stop_event: asyncio.Event) -> None:
    # In production, this should run via Celery + Redis.
    # Keeping an in-process worker for local/dev parity and simple deployments.
    logger.info("Alert worker started with interval=%s", settings.alert_generation_interval_seconds)
    while not stop_event.is_set():
        try:
            async with SessionLocal() as session:
                alert = await generate_random_alert(session)
                await process_alert(session, alert)
        except Exception:
            logger.exception("Worker iteration failed")
        try:
            await asyncio.wait_for(
                stop_event.wait(), timeout=settings.alert_generation_interval_seconds
            )
        except asyncio.TimeoutError:
            continue
    logger.info("Alert worker stopped")
