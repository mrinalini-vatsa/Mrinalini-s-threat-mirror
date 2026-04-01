from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Enrichment(Base):
    __tablename__ = "enrichments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"), index=True)
    reputation_score: Mapped[int] = mapped_column(Integer, default=0)
    country: Mapped[str] = mapped_column(String(64), default="Unknown")
    isp: Mapped[str] = mapped_column(String(128), default="Unknown")
    source: Mapped[str] = mapped_column(String(32), default="AbuseIPDB")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    alert = relationship("Alert", back_populates="enrichments")
