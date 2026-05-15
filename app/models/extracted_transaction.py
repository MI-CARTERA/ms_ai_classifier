from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ExtractedTransaction(Base):
    __tablename__ = "ai_extracted_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    classification_job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ai_classification_jobs.id", ondelete="CASCADE"),
        index=True,
    )
    sequence: Mapped[int] = mapped_column(Integer, index=True)
    transaction_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    description: Mapped[str] = mapped_column(String(512))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str | None] = mapped_column(String(16), nullable=True)
    balance: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
