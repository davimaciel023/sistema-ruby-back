from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.security import CurrentMember, DbSession
from app.models.task import BandTask, TaskComment, TaskStatus
from app.schemas.task import CommentCreate, CommentOut, TaskCreate, TaskOut, TaskUpdate

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


async def _get_task(db, task_id: int) -> BandTask:
    result = await db.execute(select(BandTask).where(BandTask.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada")
    return task


@router.get("", response_model=list[TaskOut])
async def list_tasks(
    _: CurrentMember,
    db: DbSession,
    assignee_id: int | None = None,
    status_filter: TaskStatus | None = None,
    category: str | None = None,
):
    query = select(BandTask).order_by(BandTask.due_at)
    if assignee_id is not None:
        query = query.where(BandTask.assignee_id == assignee_id)
    if status_filter is not None:
        query = query.where(BandTask.status == status_filter)
    if category is not None:
        query = query.where(BandTask.category == category)
    result = await db.execute(query)
    return result.scalars().unique().all()


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate, current: CurrentMember, db: DbSession):
    task = BandTask(**payload.model_dump(), creator_id=current.id)
    db.add(task)
    await db.commit()
    return await _get_task(db, task.id)


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(task_id: int, payload: TaskUpdate, current: CurrentMember, db: DbSession):
    task = await _get_task(db, task_id)
    # RN01: só o responsável (ou quem criou) edita/conclui a tarefa
    if current.id not in (task.assignee_id, task.creator_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só o responsável pode editar esta tarefa — você pode comentar nela",
        )
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(task, field, value)
    if data.get("status") == TaskStatus.done and task.completed_at is None:
        task.completed_at = datetime.now(timezone.utc)
    if data.get("status") in (TaskStatus.todo, TaskStatus.in_progress):
        task.completed_at = None
    await db.commit()
    return await _get_task(db, task_id)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, current: CurrentMember, db: DbSession):
    task = await _get_task(db, task_id)
    if current.id not in (task.assignee_id, task.creator_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Só o responsável pode excluir esta tarefa"
        )
    await db.delete(task)
    await db.commit()


@router.post("/{task_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def add_comment(task_id: int, payload: CommentCreate, current: CurrentMember, db: DbSession):
    await _get_task(db, task_id)
    comment = TaskComment(task_id=task_id, author_id=current.id, text=payload.text)
    db.add(comment)
    await db.commit()
    result = await db.execute(select(TaskComment).where(TaskComment.id == comment.id))
    return result.scalar_one()
