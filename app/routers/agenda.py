from datetime import date, datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, select

from app.core.security import CurrentMember, DbSession
from app.models.agenda import Event, EventType, PaymentStatus
from app.models.finance import CachePayout, EntryType, EventCost, FinanceEntry
from app.models.member import Member
from app.schemas.agenda import CostIn, EventCreate, EventOut, EventUpdate, PayoutIn

router = APIRouter(prefix="/api/events", tags=["agenda"])


async def _get_event(db, event_id: int) -> Event:
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado")
    return event


async def _apply_payouts(db, event: Event, payouts_in: list[PayoutIn] | None) -> None:
    """RN07: uma parte por integrante ativo; valores definidos manualmente.

    Sem valores informados, a divisão igual do cachê entra apenas como sugestão inicial.
    """
    result = await db.execute(select(Member).where(Member.active).order_by(Member.id))
    members = result.scalars().all()
    if not members:
        return
    amounts = {p.member_id: p.amount for p in payouts_in} if payouts_in else {}
    default = round(float(event.fee) / len(members), 2) if event.fee is not None else 0.0
    payouts_result = await db.execute(
        select(CachePayout).where(CachePayout.event_id == event.id)
    )
    existing = {p.member_id: p for p in payouts_result.scalars().all()}
    for member in members:
        payout = existing.get(member.id)
        if payout is None:
            db.add(
                CachePayout(
                    event_id=event.id,
                    member_id=member.id,
                    amount=amounts.get(member.id, default),
                )
            )
        elif member.id in amounts:
            payout.amount = amounts[member.id]


@router.get("", response_model=list[EventOut])
async def list_events(
    _: CurrentMember,
    db: DbSession,
    start: date | None = None,
    end: date | None = None,
    type_filter: EventType | None = None,
):
    query = select(Event).order_by(Event.date, Event.start_time)
    if start is not None:
        query = query.where(Event.date >= start)
    if end is not None:
        query = query.where(Event.date <= end)
    if type_filter is not None:
        query = query.where(Event.type == type_filter)
    result = await db.execute(query)
    return result.scalars().unique().all()


@router.post("", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def create_event(payload: EventCreate, _: CurrentMember, db: DbSession):
    data = payload.model_dump(exclude={"payouts", "costs"})
    event = Event(**data)
    if event.type == EventType.show and event.fee is not None:
        event.payment_status = PaymentStatus.pending
    db.add(event)
    await db.flush()
    if event.type == EventType.show:
        await _apply_payouts(db, event, payload.payouts)
        for cost in payload.costs:
            db.add(EventCost(event_id=event.id, description=cost.description, amount=cost.amount))
    await db.commit()
    return await _get_event(db, event.id)


@router.patch("/{event_id}", response_model=EventOut)
async def update_event(event_id: int, payload: EventUpdate, current: CurrentMember, db: DbSession):
    event = await _get_event(db, event_id)
    data = payload.model_dump(exclude_unset=True)
    payouts_in = data.pop("payouts", None)
    old_status = event.payment_status
    for field, value in data.items():
        setattr(event, field, value)

    if event.type == EventType.show:
        if payouts_in is not None:
            await _apply_payouts(db, event, [PayoutIn(**p) for p in payouts_in])
        # RN06: cachê só entra no caixa quando marcado como recebido
        if (
            data.get("payment_status") == PaymentStatus.received
            and old_status != PaymentStatus.received
            and event.fee is not None
        ):
            db.add(
                FinanceEntry(
                    type=EntryType.income,
                    category="cachê",
                    description=f"Cachê do show: {event.title}",
                    amount=event.fee,
                    date=event.date,
                    event_id=event.id,
                    created_by_id=current.id,
                )
            )
    await db.commit()
    return await _get_event(db, event_id)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: int, _: CurrentMember, db: DbSession):
    event = await _get_event(db, event_id)
    await db.delete(event)
    await db.commit()


@router.patch("/{event_id}/payouts/{payout_id}", response_model=EventOut)
async def toggle_payout(
    event_id: int, payout_id: int, received: bool, current: CurrentMember, db: DbSession
):
    """Marca/desmarca o pagamento da parte do integrante — pago vira despesa automática."""
    result = await db.execute(
        select(CachePayout).where(CachePayout.id == payout_id, CachePayout.event_id == event_id)
    )
    payout = result.scalar_one_or_none()
    if payout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Divisão não encontrada")
    event = await _get_event(db, event_id)
    payout.received = received
    payout.received_at = datetime.now(timezone.utc) if received else None
    if received:
        db.add(
            FinanceEntry(
                type=EntryType.expense,
                category="cachê — integrantes",
                description=f"Parte de {payout.member.name} — {event.title}",
                amount=payout.amount,
                date=event.date,
                event_id=event.id,
                payout_id=payout.id,
                created_by_id=current.id,
            )
        )
    else:
        await db.execute(delete(FinanceEntry).where(FinanceEntry.payout_id == payout.id))
    await db.commit()
    return await _get_event(db, event_id)


@router.post("/{event_id}/costs", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def add_cost(event_id: int, payload: CostIn, _: CurrentMember, db: DbSession):
    """Adiciona um custo de parceria ao show (som, iluminação, transporte…)."""
    event = await _get_event(db, event_id)
    db.add(EventCost(event_id=event.id, description=payload.description, amount=payload.amount))
    await db.commit()
    return await _get_event(db, event_id)


@router.patch("/{event_id}/costs/{cost_id}", response_model=EventOut)
async def toggle_cost(
    event_id: int, cost_id: int, paid: bool, current: CurrentMember, db: DbSession
):
    """Marca/desmarca o pagamento de um custo — pago vira despesa automática."""
    result = await db.execute(
        select(EventCost).where(EventCost.id == cost_id, EventCost.event_id == event_id)
    )
    cost = result.scalar_one_or_none()
    if cost is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custo não encontrado")
    event = await _get_event(db, event_id)
    cost.paid = paid
    cost.paid_at = datetime.now(timezone.utc) if paid else None
    if paid:
        db.add(
            FinanceEntry(
                type=EntryType.expense,
                category="custo de show",
                description=f"{cost.description} — {event.title}",
                amount=cost.amount,
                date=event.date,
                event_id=event.id,
                cost_id=cost.id,
                created_by_id=current.id,
            )
        )
    else:
        await db.execute(delete(FinanceEntry).where(FinanceEntry.cost_id == cost.id))
    await db.commit()
    return await _get_event(db, event_id)


@router.delete("/{event_id}/costs/{cost_id}", response_model=EventOut)
async def delete_cost(event_id: int, cost_id: int, _: CurrentMember, db: DbSession):
    result = await db.execute(
        select(EventCost).where(EventCost.id == cost_id, EventCost.event_id == event_id)
    )
    cost = result.scalar_one_or_none()
    if cost is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custo não encontrado")
    await db.execute(delete(FinanceEntry).where(FinanceEntry.cost_id == cost.id))
    await db.delete(cost)
    await db.commit()
    return await _get_event(db, event_id)
