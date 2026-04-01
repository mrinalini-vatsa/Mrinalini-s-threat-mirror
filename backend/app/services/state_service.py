from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert_state import AlertState
from app.models.enums import AlertStateType


async def add_state(session: AsyncSession, alert_id: int, state: AlertStateType, notes: str = "") -> None:
    session.add(AlertState(alert_id=alert_id, state=state, notes=notes))
    await session.flush()
