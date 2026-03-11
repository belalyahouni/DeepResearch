"""SQLAlchemy model for community paper activity tracking."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CommunityPaper(Base):
    __tablename__ = "community_papers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    arxiv_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    interaction_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_interacted_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
