from datetime import datetime

from pydantic import BaseModel, Field

from app.models.task import TaskPriority, TaskStatus
from app.schemas.common import MemberBrief, ORMModel


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    assignee_id: int
    due_at: datetime
    priority: TaskPriority = TaskPriority.medium
    category: str = "geral"


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    due_at: datetime | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    category: str | None = None


class CommentCreate(BaseModel):
    text: str = Field(min_length=1)


class CommentOut(ORMModel):
    id: int
    text: str
    created_at: datetime
    author: MemberBrief


class TaskOut(ORMModel):
    id: int
    title: str
    description: str
    due_at: datetime
    priority: TaskPriority
    status: TaskStatus
    category: str
    created_at: datetime
    completed_at: datetime | None
    assignee: MemberBrief
    creator: MemberBrief
    comments: list[CommentOut] = []
