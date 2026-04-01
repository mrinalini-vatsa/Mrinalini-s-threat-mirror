from pydantic import BaseModel


class MetricsOut(BaseModel):
    total_alerts: int
    failures: int
    alerts_blocked_count: int
    avg_processing_time_ms: float
    severity_distribution: dict[str, int]
