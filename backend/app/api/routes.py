from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.alert import Alert
from app.models.correlation import Correlation
from app.models.enums import AlertStateType
from app.schemas.alert import AlertResponse
from app.schemas.detail import AlertDetailOut, CorrelationOut, DecisionOut, EnrichmentOut, StateOut
from app.schemas.metrics import MetricsOut
from app.services.alert_pipeline import get_severity_distribution
from app.services.metrics_service import metrics_store
from app.services.report_service import generate_incident_report
from app.services.state_service import add_state

router = APIRouter(prefix="/api", tags=["threatmirror"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(db: AsyncSession = Depends(get_db)) -> list[Alert]:
    result = await db.execute(select(Alert).order_by(Alert.created_at.desc()).limit(200))
    return list(result.scalars().all())


@router.get("/alerts/{alert_id}", response_model=AlertDetailOut)
async def get_alert_detail(alert_id: int, db: AsyncSession = Depends(get_db)) -> AlertDetailOut:
    result = await db.execute(
        select(Alert)
        .where(Alert.id == alert_id)
        .options(selectinload(Alert.enrichments), selectinload(Alert.decisions), selectinload(Alert.states))
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    related = await db.execute(select(Correlation).where(Correlation.alert_id == alert_id))
    related_items = [CorrelationOut.model_validate(item) for item in related.scalars().all()]

    return AlertDetailOut(
        id=alert.id,
        ip_address=alert.ip_address,
        user_id=alert.user_id,
        event_type=alert.event_type,
        severity=alert.severity.value,
        created_at=alert.created_at,
        enrichments=[EnrichmentOut.model_validate(e) for e in alert.enrichments],
        decisions=[DecisionOut.model_validate(d) for d in alert.decisions],
        timeline=[StateOut.model_validate(s) for s in alert.states],
        related_alerts=related_items,
    )


@router.get("/metrics", response_model=MetricsOut)
async def get_metrics(db: AsyncSession = Depends(get_db)) -> MetricsOut:
    total_alerts = await db.scalar(select(func.count(Alert.id)))
    severity_distribution = await get_severity_distribution(db)
    failures, avg_time, blocked = await metrics_store.snapshot()
    return MetricsOut(
        total_alerts=total_alerts or 0,
        failures=failures,
        alerts_blocked_count=blocked,
        avg_processing_time_ms=avg_time,
        severity_distribution=severity_distribution,
    )


@router.get("/alerts/{alert_id}/report")
async def get_report(alert_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    detail = await get_alert_detail(alert_id, db)
    latest_decision = detail.decisions[-1].decision if detail.decisions else "UNKNOWN"
    report = await generate_incident_report(
        {
            "alert_id": detail.id,
            "summary": {"ip_address": detail.ip_address, "event_type": detail.event_type},
            "decision": latest_decision,
            "evidence": {
                "enrichment": [e.model_dump() for e in detail.enrichments],
                "timeline": [t.model_dump() for t in detail.timeline],
                "correlations": [c.model_dump() for c in detail.related_alerts],
            },
        }
    )
    return {"report": report}


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await add_state(db, alert_id, AlertStateType.resolved, "Resolved by SOC analyst")
    await db.commit()
    return {"status": "resolved"}
