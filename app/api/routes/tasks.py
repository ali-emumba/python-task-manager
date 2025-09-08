from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.api.dependencies import get_current_user, get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, PaginatedTasks
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(task_in: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = task_service.create_task(db, current_user, task_in)
    return TaskRead.model_validate(task)

@router.get("/", response_model=PaginatedTasks)
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
    q: Optional[str] = None,
    status: Optional[str] = None,
    due_before: Optional[date] = None,
    due_after: Optional[date] = None,
    all: bool = False,
):
    total, tasks = task_service.list_tasks(
        db,
        owner=current_user,
        all_tasks=all and current_user.role == current_user.role.admin,
        q=q,
        status=status,
        due_before=due_before,
        due_after=due_after,
        limit=limit,
        offset=offset,
    )
    return PaginatedTasks(total=total, items=[TaskRead.model_validate(t) for t in tasks])

@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = task_service.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if current_user.role != current_user.role.admin and task.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return TaskRead.model_validate(task)

@router.put("/{task_id}", response_model=TaskRead)
def update_task(task_id: int, task_in: TaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = task_service.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    task = task_service.update_task(db, task=task, task_in=task_in, current_user=current_user)
    return TaskRead.model_validate(task)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = task_service.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    task_service.delete_task(db, task=task, current_user=current_user)
    return None
