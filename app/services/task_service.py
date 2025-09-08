from datetime import date
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from fastapi import HTTPException, status

from app.models.task import Task, TaskStatus
from app.models.user import User, UserRole
from app.schemas.task import TaskCreate, TaskUpdate


def create_task(db: Session, owner: User, task_in: TaskCreate) -> Task:
    task = Task(
        owner_id=owner.id,
        title=task_in.title,
        description=task_in.description,
        due_date=task_in.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task_by_id(db: Session, task_id: int) -> Task | None:
    return db.query(Task).filter(Task.id == task_id).first()


def list_tasks(
    db: Session,
    *,
    owner: User | None = None,
    all_tasks: bool = False,
    q: str | None = None,
    status: str | None = None,
    due_before: date | None = None,
    due_after: date | None = None,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[int, List[Task]]:
    query = db.query(Task)

    if not all_tasks and owner:
        query = query.filter(Task.owner_id == owner.id)

    if q:
        like = f"%{q}%"
        query = query.filter(or_(Task.title.ilike(like), Task.description.ilike(like)))

    if status:
        try:
            status_enum = TaskStatus(status)
            query = query.filter(Task.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

    if due_before:
        query = query.filter(Task.due_date != None, Task.due_date <= due_before)  # noqa: E711
    if due_after:
        query = query.filter(Task.due_date != None, Task.due_date >= due_after)  # noqa: E711

    total = query.count()
    tasks = query.order_by(Task.created_at.desc()).offset(offset).limit(limit).all()
    return total, tasks


def update_task(db: Session, *, task: Task, task_in: TaskUpdate, current_user: User) -> Task:
    if current_user.role != UserRole.admin and task.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    for field, value in task_in.model_dump(exclude_unset=True).items():
        if field == "status" and value is not None:
            try:
                value = TaskStatus(value)
            except ValueError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
        setattr(task, field, value)

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, *, task: Task, current_user: User) -> None:
    if current_user.role != UserRole.admin and task.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    db.delete(task)
    db.commit()
