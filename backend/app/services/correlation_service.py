from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.correlation import Correlation


async def correlate_alert(session: AsyncSession, alert: Alert) -> int:
    existing = await session.execute(
        select(Alert.id).where(Alert.ip_address == alert.ip_address, Alert.id != alert.id)
    )
    related_ids = [row[0] for row in existing.all()]
    total_occurrences = len(related_ids) + 1
    correlation_reason = (
        "Potential campaign: IP observed in more than 2 alerts"
        if total_occurrences > 2
        else "Repeated IP across alerts"
    )
    for related_id in related_ids:
        session.add(
            Correlation(
                alert_id=alert.id,
                related_alert_id=related_id,
                reason=correlation_reason,
                correlation_strength=total_occurrences,
            )
        )
    await session.flush()
    return len(related_ids)
