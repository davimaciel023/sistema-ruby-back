from datetime import date

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.core.security import CurrentMember, DbSession
from app.models.agenda import Event, EventType, PaymentStatus
from app.models.finance import CachePayout, EntryType, EventCost, FinanceEntry
from app.schemas.finance import EntryCreate, EntryOut, FinanceSummary

router = APIRouter(prefix="/api/finance", tags=["finance"])


@router.get("/entries", response_model=list[EntryOut])
async def list_entries(
    _: CurrentMember,
    db: DbSession,
    start: date | None = None,
    end: date | None = None,
    type_filter: EntryType | None = None,
):
    query = select(FinanceEntry).order_by(FinanceEntry.date.desc(), FinanceEntry.id.desc())
    if start is not None:
        query = query.where(FinanceEntry.date >= start)
    if end is not None:
        query = query.where(FinanceEntry.date <= end)
    if type_filter is not None:
        query = query.where(FinanceEntry.type == type_filter)
    result = await db.execute(query)
    return result.scalars().unique().all()


@router.post("/entries", response_model=EntryOut, status_code=status.HTTP_201_CREATED)
async def create_entry(payload: EntryCreate, current: CurrentMember, db: DbSession):
    entry = FinanceEntry(**payload.model_dump(), created_by_id=current.id)
    db.add(entry)
    await db.commit()
    result = await db.execute(select(FinanceEntry).where(FinanceEntry.id == entry.id))
    return result.scalar_one()


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(entry_id: int, _: CurrentMember, db: DbSession):
    result = await db.execute(select(FinanceEntry).where(FinanceEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lançamento não encontrado")
    await db.delete(entry)
    await db.commit()


@router.get("/summary", response_model=FinanceSummary)
async def summary(_: CurrentMember, db: DbSession):
    """RN08: saldo = receitas − despesas. Cachês pendentes ficam fora do saldo."""
    income = await db.scalar(
        select(func.coalesce(func.sum(FinanceEntry.amount), 0)).where(
            FinanceEntry.type == EntryType.income
        )
    )
    expense = await db.scalar(
        select(func.coalesce(func.sum(FinanceEntry.amount), 0)).where(
            FinanceEntry.type == EntryType.expense
        )
    )
    pending = await db.scalar(
        select(func.coalesce(func.sum(Event.fee), 0)).where(
            Event.type == EventType.show, Event.payment_status == PaymentStatus.pending
        )
    )
    pending_payouts = await db.scalar(
        select(func.coalesce(func.sum(CachePayout.amount), 0))
        .join(Event, Event.id == CachePayout.event_id)
        .where(
            CachePayout.received.is_(False),
            Event.payment_status == PaymentStatus.received,
        )
    )
    pending_costs = await db.scalar(
        select(func.coalesce(func.sum(EventCost.amount), 0))
        .join(Event, Event.id == EventCost.event_id)
        .where(
            EventCost.paid.is_(False),
            Event.payment_status == PaymentStatus.received,
        )
    )
    return FinanceSummary(
        total_income=float(income),
        total_expense=float(expense),
        balance=float(income) - float(expense),
        pending_fees=float(pending),
        pending_payouts=float(pending_payouts),
        pending_costs=float(pending_costs),
    )
