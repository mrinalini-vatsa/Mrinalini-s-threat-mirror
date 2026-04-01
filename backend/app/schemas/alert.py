from datetime import datetime

from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: int
    ip_address: str
    user_id: str
    event_type: str
    severity: str
    created_at: datetime

    class Config:
        from_attributes = True
