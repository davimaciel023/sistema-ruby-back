from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.config import settings
from app.core.security import CurrentMember, DbSession
from app.models.member import Member
from app.models.timelog import TimeLog
from app.schemas.common import MemberBrief
from app.schemas.timelog import CheckInRequest, DaySummary, MemberHoursReport, TimeLogOut

router = APIRouter(prefix="/api/timelogs", tags=["timelogs"])


@router.get("/open", response_model=TimeLogOut | None)
async def open_session(current: CurrentMember, db: DbSession):
    """Sessão em andamento (entrada sem saída) do integrante logado."""
    result = await db.execute(
        select(TimeLog).where(TimeLog.member_id == current.id, TimeLog.check_out.is_(None))
    )
    return result.scalars().first()


@router.post("/check-in", response_model=TimeLogOut, status_code=status.HTTP_201_CREATED)
async def check_in(payload: CheckInRequest, current: CurrentMember, db: DbSession):
    result = await db.execute(
        select(TimeLog).where(TimeLog.member_id == current.id, TimeLog.check_out.is_(None))
    )
    if result.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Você já tem uma sessão aberta — registre a saída primeiro",
        )
    now = datetime.now(timezone.utc)
    log = TimeLog(
        member_id=current.id,
        date=now.date(),
        check_in=now,
        category=payload.category,
        description=payload.description,
    )
    db.add(log)
    await db.commit()
    result = await db.execute(select(TimeLog).where(TimeLog.id == log.id))
    return result.scalar_one()


@router.post("/check-out", response_model=TimeLogOut)
async def check_out(current: CurrentMember, db: DbSession):
    result = await db.execute(
        select(TimeLog).where(TimeLog.member_id == current.id, TimeLog.check_out.is_(None))
    )
    log = result.scalars().first()
    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma sessão aberta para encerrar"
        )
    log.check_out = datetime.now(timezone.utc)
    await db.commit()
    result = await db.execute(select(TimeLog).where(TimeLog.id == log.id))
    return result.scalar_one()


@router.get("", response_model=list[TimeLogOut])
async def list_logs(
    _: CurrentMember,
    db: DbSession,
    member_id: int | None = None,
    start: date | None = None,
    end: date | None = None,
):
    query = select(TimeLog).order_by(TimeLog.check_in.desc())
    if member_id is not None:
        query = query.where(TimeLog.member_id == member_id)
    if start is not None:
        query = query.where(TimeLog.date >= start)
    if end is not None:
        query = query.where(TimeLog.date <= end)
    result = await db.execute(query)
    return result.scalars().unique().all()


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log(log_id: int, current: CurrentMember, db: DbSession):
    result = await db.execute(select(TimeLog).where(TimeLog.id == log_id))
    log = result.scalar_one_or_none()
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro não encontrado")
    if log.member_id != current.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Só é possível excluir seus próprios registros"
        )
    await db.delete(log)
    await db.commit()


@router.get("/report", response_model=list[MemberHoursReport])
async def report(_: CurrentMember, db: DbSession, start: date | None = None, end: date | None = None):
    """Horas por integrante e por dia, com meta diária de 1h30 (RN05 revisada: meta diária)."""
    if end is None:
        end = date.today()
    if start is None:
        start = end - timedelta(days=6)

    members_result = await db.execute(select(Member).where(Member.active).order_by(Member.id))
    members = members_result.scalars().all()

    logs_result = await db.execute(
        select(TimeLog).where(
            TimeLog.date >= start, TimeLog.date <= end, TimeLog.check_out.is_not(None)
        )
    )
    logs = logs_result.scalars().all()

    reports: list[MemberHoursReport] = []
    for member in members:
        days: list[DaySummary] = []
        total = 0
        current_day = start
        while current_day <= end:
            minutes = sum(
                log.duration_minutes or 0
                for log in logs
                if log.member_id == member.id and log.date == current_day
            )
            total += minutes
            days.append(
                DaySummary(
                    date=current_day,
                    total_minutes=minutes,
                    goal_minutes=settings.daily_goal_minutes,
                    goal_met=minutes >= settings.daily_goal_minutes,
                )
            )
            current_day += timedelta(days=1)
        reports.append(
            MemberHoursReport(
                member=MemberBrief.model_validate(member), days=days, total_minutes=total
            )
        )
    return reports
