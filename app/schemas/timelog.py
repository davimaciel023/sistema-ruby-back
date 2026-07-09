from datetime import date, datetime

from pydantic import BaseModel

from app.models.timelog import TimeLogCategory
from app.schemas.common import MemberBrief, ORMModel


class CheckInRequest(BaseModel):
    category: TimeLogCategory = TimeLogCategory.work
    description: str = ""


class TimeLogOut(ORMModel):
    id: int
    date: date
    check_in: datetime
    check_out: datetime | None
    category: TimeLogCategory
    description: str
    duration_minutes: int | None
    member: MemberBrief


class DaySummary(BaseModel):
    date: date
    total_minutes: int
    goal_minutes: int
    goal_met: bool


class MemberHoursReport(BaseModel):
    member: MemberBrief
    days: list[DaySummary]
    total_minutes: int
