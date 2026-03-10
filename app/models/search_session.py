from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SearchSession(Base):
    __tablename__ = "search_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    original_query: Mapped[str] = mapped_column(String, nullable=False)
    topic_category: Mapped[str | None] = mapped_column(String, nullable=True)
    refined_query: Mapped[str | None] = mapped_column(String, nullable=True)
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
