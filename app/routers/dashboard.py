from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.core.config import settings
from app.core.security import CurrentMember, DbSession
from app.models.agenda import Event
from app.models.task import BandTask, TaskStatus
from app.schemas.agenda import EventOut
from app.schemas.task import TaskOut

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class TaskAlert(BaseModel):
    task: TaskOut
    level: str  # overdue | urgent | warning


class DashboardOut(BaseModel):
    alerts: list[TaskAlert]
    my_pending_tasks: list[TaskOut]
    upcoming_events: list[EventOut]


@router.get("", response_model=DashboardOut)
async def dashboard(current: CurrentMember, db: DbSession):
    now = datetime.now(timezone.utc)
    warning_limit = now + timedelta(hours=settings.alert_warning_hours)
    urgent_limit = now + timedelta(hours=settings.alert_urgent_hours)

    # RN03/RN04: alertas de prazo (vencida, ≤24h, ≤48h) de todas as tarefas abertas
    result = await db.execute(
        select(BandTask)
        .where(BandTask.status != TaskStatus.done, BandTask.due_at <= warning_limit)
        .order_by(BandTask.due_at)
    )
    alerts = []
    for task in result.scalars().unique().all():
        due = task.due_at if task.due_at.tzinfo else task.due_at.replace(tzinfo=timezone.utc)
        if due < now:
            level = "overdue"
        elif due <= urgent_limit:
            level = "urgent"
        else:
            level = "warning"
        alerts.append(TaskAlert(task=TaskOut.model_validate(task), level=level))

    result = await db.execute(
        select(BandTask)
        .where(BandTask.assignee_id == current.id, BandTask.status != TaskStatus.done)
        .order_by(BandTask.due_at)
        .limit(10)
    )
    my_tasks = result.scalars().unique().all()

    result = await db.execute(
        select(Event)
        .where(Event.date >= date.today())
        .order_by(Event.date, Event.start_time)
        .limit(8)
    )
    events = result.scalars().unique().all()

    return DashboardOut(
        alerts=alerts,
        my_pending_tasks=[TaskOut.model_validate(t) for t in my_tasks],
        upcoming_events=[EventOut.model_validate(e) for e in events],
    )
