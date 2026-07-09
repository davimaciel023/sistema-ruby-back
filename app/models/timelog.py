import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TimeLogCategory(str, enum.Enum):
    work = "work"
    study = "study"


class TimeLog(Base):
    """Sessão de trabalho/estudo (entrada e saída). Meta diária: 1h30."""

    __tablename__ = "time_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    check_in: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    check_out: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    category: Mapped[TimeLogCategory] = mapped_column(
        Enum(TimeLogCategory), default=TimeLogCategory.work
    )
    description: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    member = relationship("Member", lazy="joined")

    @property
    def duration_minutes(self) -> int | None:
        if self.check_out is None:
            return None
        return int((self.check_out - self.check_in).total_seconds() // 60)
