import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EntryType(str, enum.Enum):
    income = "income"
    expense = "expense"


class FinanceEntry(Base):
    """Lançamento financeiro. Cachês recebidos entram como income ligados ao show."""

    __tablename__ = "finance_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[EntryType] = mapped_column(Enum(EntryType))
    category: Mapped[str] = mapped_column(String(100))  # cachê, transporte, equipamento…
    description: Mapped[str] = mapped_column(String(255), default="")
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    date: Mapped[date] = mapped_column(Date, index=True)
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL"), nullable=True
    )
    payout_id: Mapped[int | None] = mapped_column(
        ForeignKey("cache_payouts.id", ondelete="SET NULL"), nullable=True
    )
    cost_id: Mapped[int | None] = mapped_column(
        ForeignKey("event_costs.id", ondelete="SET NULL"), nullable=True
    )
    created_by_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    created_by = relationship("Member", lazy="joined")


class CachePayout(Base):
    """Parte de cada integrante no cachê de um show (valores definidos manualmente)."""

    __tablename__ = "cache_payouts"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    received: Mapped[bool] = mapped_column(Boolean, default=False)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    member = relationship("Member", lazy="joined")


class EventCost(Base):
    """Custo de parceria de um show (som, iluminação, transporte contratado…)."""

    __tablename__ = "event_costs"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    description: Mapped[str] = mapped_column(String(200))
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    paid: Mapped[bool] = mapped_column(Boolean, default=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
