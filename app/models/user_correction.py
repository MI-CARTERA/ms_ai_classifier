from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class UserCorrection(Base):
    __tablename__ = "ai_user_corrections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    classification_result_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ai_classification_results.id", ondelete="CASCADE"),
        index=True,
    )
    corrected_movement_type: Mapped[str] = mapped_column(String(64))
    corrected_category: Mapped[str] = mapped_column(String(128))
    correction_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
