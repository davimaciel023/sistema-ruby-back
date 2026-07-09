import enum
from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, Enum, Numeric, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EventType(str, enum.Enum):
    show = "show"
    rehearsal = "rehearsal"       # ensaio
    reminder = "reminder"         # lembrete
    fixed_activity = "fixed"      # atividade fixa (recorrente)


class Recurrence(str, enum.Enum):
    none = "none"
    weekly = "weekly"
    biweekly = "biweekly"
    monthly = "monthly"


class PaymentStatus(str, enum.Enum):
    pending = "pending"    # a receber
    received = "received"  # recebido


class Event(Base):
    """Evento da agenda. Quando type == show, os campos de show são usados."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[EventType] = mapped_column(Enum(EventType))
    title: Mapped[str] = mapped_column(String(200))
    date: Mapped[date] = mapped_column(Date, index=True)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    location: Mapped[str] = mapped_column(String(255), default="")
    recurrence: Mapped[Recurrence] = mapped_column(Enum(Recurrence), default=Recurrence.none)
    notes: Mapped[str] = mapped_column(Text, default="")

    # Campos de show
    contractor: Mapped[str] = mapped_column(String(200), default="")
    contractor_contact: Mapped[str] = mapped_column(String(200), default="")
    fee: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)  # cachê
    payment_status: Mapped[PaymentStatus | None] = mapped_column(
        Enum(PaymentStatus), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    payouts = relationship(
        "CachePayout", lazy="selectin", cascade="all, delete-orphan", order_by="CachePayout.member_id"
    )
    costs = relationship(
        "EventCost", lazy="selectin", cascade="all, delete-orphan", order_by="EventCost.id"
    )
