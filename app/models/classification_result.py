from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ClassificationResult(Base):
    __tablename__ = "ai_classification_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    classification_job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ai_classification_jobs.id", ondelete="CASCADE"),
        index=True,
    )
    extracted_transaction_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ai_extracted_transactions.id", ondelete="CASCADE"),
        index=True,
    )
    movement_type: Mapped[str] = mapped_column(String(64))
    category: Mapped[str] = mapped_column(String(128))
    confidence: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
