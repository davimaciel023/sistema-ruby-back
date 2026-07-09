import datetime as dt
from datetime import date, datetime, time

from pydantic import BaseModel, Field

from app.models.agenda import EventType, PaymentStatus, Recurrence
from app.schemas.common import MemberBrief, ORMModel


class PayoutIn(BaseModel):
    member_id: int
    amount: float = Field(ge=0)


class CostIn(BaseModel):
    description: str = Field(min_length=1, max_length=200)
    amount: float = Field(gt=0)


class EventCreate(BaseModel):
    type: EventType
    title: str = Field(min_length=1, max_length=200)
    date: date
    start_time: time | None = None
    end_time: time | None = None
    location: str = ""
    recurrence: Recurrence = Recurrence.none
    notes: str = ""
    contractor: str = ""
    contractor_contact: str = ""
    fee: float | None = None
    payouts: list[PayoutIn] | None = None
    costs: list[CostIn] = []


class EventUpdate(BaseModel):
    type: EventType | None = None
    title: str | None = None
    date: dt.date | None = None
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = None
    recurrence: Recurrence | None = None
    notes: str | None = None
    contractor: str | None = None
    contractor_contact: str | None = None
    fee: float | None = None
    payment_status: PaymentStatus | None = None
    payouts: list[PayoutIn] | None = None


class PayoutOut(ORMModel):
    id: int
    member: MemberBrief
    amount: float
    received: bool
    received_at: datetime | None


class CostOut(ORMModel):
    id: int
    description: str
    amount: float
    paid: bool
    paid_at: datetime | None


class EventOut(ORMModel):
    id: int
    type: EventType
    title: str
    date: date
    start_time: time | None
    end_time: time | None
    location: str
    recurrence: Recurrence
    notes: str
    contractor: str
    contractor_contact: str
    fee: float | None
    payment_status: PaymentStatus | None
    payouts: list[PayoutOut] = []
    costs: list[CostOut] = []
