from datetime import datetime

from pydantic import BaseModel


class EnrichmentOut(BaseModel):
    reputation_score: int
    country: str
    isp: str
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


class DecisionOut(BaseModel):
    decision: str
    confidence: float
    score: int
    reasons: list[str]
    created_at: datetime

    class Config:
        from_attributes = True


class StateOut(BaseModel):
    state: str
    notes: str
    created_at: datetime

    class Config:
        from_attributes = True


class CorrelationOut(BaseModel):
    related_alert_id: int
    reason: str
    correlation_strength: int
    created_at: datetime

    class Config:
        from_attributes = True


class AlertDetailOut(BaseModel):
    id: int
    ip_address: str
    user_id: str
    event_type: str
    severity: str
    created_at: datetime
    enrichments: list[EnrichmentOut]
    decisions: list[DecisionOut]
    timeline: list[StateOut]
    related_alerts: list[CorrelationOut]
