from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.api.dependencies import get_current_user, get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, PaginatedTasks
from app.services import task_service
from app.core.logging import log_business_step

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(task_in: TaskCreate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    log_business_step(
        "task_creation_start",
        {
            "title": task_in.title,
            "has_description": bool(task_in.description),
            "has_due_date": bool(task_in.due_date),
            "description_length": len(task_in.description) if task_in.description else 0
        },
        request=request,
        user_id=current_user.id
    )
    
    try:
        log_business_step(
            "task_validation_start",
            {
                "title_length": len(task_in.title),
                "due_date": str(task_in.due_date) if task_in.due_date else None
            },
            request=request,
            user_id=current_user.id
        )
        
        task = task_service.create_task(db, current_user, task_in)
        
        log_business_step(
            "task_created_successfully",
            {
                "task_id": task.id,
                "title": task.title,
                "status": task.status.value,
                "owner_id": task.owner_id,
                "due_date": str(task.due_date) if task.due_date else None
            },
            request=request,
            user_id=current_user.id
        )
        
        return TaskRead.model_validate(task)
        
    except Exception as e:
        log_business_step(
            "task_creation_failed",
            {
                "title": task_in.title,
                "error": str(e),
                "error_type": type(e).__name__
            },
            request=request,
            user_id=current_user.id,
            level="error"
        )
        raise

@router.get("/", response_model=PaginatedTasks)
def list_tasks(
    request: Request,
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
    log_business_step(
        "task_list_request_start",
        {
            "limit": limit,
            "offset": offset,
            "search_query": q,
            "status_filter": status,
            "due_before": str(due_before) if due_before else None,
            "due_after": str(due_after) if due_after else None,
            "admin_view": all,
            "user_role": current_user.role.value
        },
        request=request,
        user_id=current_user.id
    )
    
    try:
        log_business_step(
            "task_query_execution_start",
            {
                "is_admin_request": all and current_user.role == current_user.role.admin,
                "filters_applied": {
                    "search": bool(q),
                    "status": bool(status),
                    "date_range": bool(due_before or due_after)
                }
            },
            request=request,
            user_id=current_user.id
        )
        
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
        
        log_business_step(
            "task_list_completed",
            {
                "total_tasks": total,
                "returned_tasks": len(tasks),
                "has_more": total > (offset + len(tasks)),
                "page_info": {
                    "current_page": (offset // limit) + 1,
                    "total_pages": (total + limit - 1) // limit
                }
            },
            request=request,
            user_id=current_user.id
        )
        
        return PaginatedTasks(total=total, items=[TaskRead.model_validate(t) for t in tasks])
        
    except Exception as e:
        log_business_step(
            "task_list_failed",
            {
                "error": str(e),
                "error_type": type(e).__name__,
                "query_params": {
                    "limit": limit,
                    "offset": offset,
                    "q": q,
                    "status": status
                }
            },
            request=request,
            user_id=current_user.id,
            level="error"
        )
        raise

@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    log_business_step(
        "task_get_request_start",
        {"task_id": task_id},
        request=request,
        user_id=current_user.id
    )
    
    try:
        log_business_step(
            "task_lookup_start",
            {"task_id": task_id},
            request=request,
            user_id=current_user.id
        )
        
        task = task_service.get_task_by_id(db, task_id)
        if not task:
            log_business_step(
                "task_not_found",
                {"task_id": task_id},
                request=request,
                user_id=current_user.id,
                level="warning"
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        
        log_business_step(
            "task_authorization_check",
            {
                "task_id": task_id,
                "task_owner_id": task.owner_id,
                "requesting_user_id": current_user.id,
                "user_role": current_user.role.value,
                "is_owner": task.owner_id == current_user.id,
                "is_admin": current_user.role == current_user.role.admin
            },
            request=request,
            user_id=current_user.id
        )
        
        if current_user.role != current_user.role.admin and task.owner_id != current_user.id:
            log_business_step(
                "task_access_denied",
                {
                    "task_id": task_id,
                    "task_owner_id": task.owner_id,
                    "requesting_user_id": current_user.id,
                    "reason": "not_owner_or_admin"
                },
                request=request,
                user_id=current_user.id,
                level="warning"
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
        log_business_step(
            "task_retrieved_successfully",
            {
                "task_id": task.id,
                "title": task.title,
                "status": task.status.value,
                "owner_id": task.owner_id,
                "access_type": "admin_view" if current_user.role == current_user.role.admin and task.owner_id != current_user.id else "owner_view"
            },
            request=request,
            user_id=current_user.id
        )
        
        return TaskRead.model_validate(task)
        
    except HTTPException:
        # Re-raise HTTP exceptions (already logged above)
        raise
    except Exception as e:
        log_business_step(
            "task_get_failed",
            {
                "task_id": task_id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            request=request,
            user_id=current_user.id,
            level="error"
        )
        raise

@router.put("/{task_id}", response_model=TaskRead)
def update_task(task_id: int, task_in: TaskUpdate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    log_business_step(
        "task_update_request_start",
        {
            "task_id": task_id,
            "updates": {
                "title": task_in.title,
                "description": task_in.description,
                "due_date": str(task_in.due_date) if task_in.due_date else None,
                "status": task_in.status
            },
            "fields_to_update": [field for field, value in task_in.model_dump(exclude_unset=True).items() if value is not None]
        },
        request=request,
        user_id=current_user.id
    )
    
    try:
        log_business_step(
            "task_lookup_for_update",
            {"task_id": task_id},
            request=request,
            user_id=current_user.id
        )
        
        task = task_service.get_task_by_id(db, task_id)
        if not task:
            log_business_step(
                "task_update_failed_not_found",
                {"task_id": task_id},
                request=request,
                user_id=current_user.id,
                level="warning"
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        
        log_business_step(
            "task_update_before_state",
            {
                "task_id": task.id,
                "current_title": task.title,
                "current_status": task.status.value,
                "current_due_date": str(task.due_date) if task.due_date else None,
                "owner_id": task.owner_id
            },
            request=request,
            user_id=current_user.id
        )
        
        updated_task = task_service.update_task(db, task=task, task_in=task_in, current_user=current_user)
        
        log_business_step(
            "task_updated_successfully",
            {
                "task_id": updated_task.id,
                "changes": {
                    "title": {"old": task.title, "new": updated_task.title} if task.title != updated_task.title else None,
                    "status": {"old": task.status.value, "new": updated_task.status.value} if task.status != updated_task.status else None,
                    "due_date": {
                        "old": str(task.due_date) if task.due_date else None,
                        "new": str(updated_task.due_date) if updated_task.due_date else None
                    } if task.due_date != updated_task.due_date else None
                },
                "updated_by": current_user.id
            },
            request=request,
            user_id=current_user.id
        )
        
        return TaskRead.model_validate(updated_task)
        
    except HTTPException:
        # Re-raise HTTP exceptions (already logged above)
        raise
    except Exception as e:
        log_business_step(
            "task_update_failed",
            {
                "task_id": task_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "attempted_updates": task_in.model_dump(exclude_unset=True)
            },
            request=request,
            user_id=current_user.id,
            level="error"
        )
        raise

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    log_business_step(
        "task_delete_request_start",
        {"task_id": task_id},
        request=request,
        user_id=current_user.id
    )
    
    try:
        log_business_step(
            "task_lookup_for_deletion",
            {"task_id": task_id},
            request=request,
            user_id=current_user.id
        )
        
        task = task_service.get_task_by_id(db, task_id)
        if not task:
            log_business_step(
                "task_delete_failed_not_found",
                {"task_id": task_id},
                request=request,
                user_id=current_user.id,
                level="warning"
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        
        log_business_step(
            "task_delete_authorization_check",
            {
                "task_id": task_id,
                "task_owner_id": task.owner_id,
                "requesting_user_id": current_user.id,
                "user_role": current_user.role.value,
                "is_owner": task.owner_id == current_user.id,
                "is_admin": current_user.role == current_user.role.admin
            },
            request=request,
            user_id=current_user.id
        )
        
        log_business_step(
            "task_delete_before_state",
            {
                "task_id": task.id,
                "title": task.title,
                "status": task.status.value,
                "owner_id": task.owner_id,
                "created_at": str(task.created_at),
                "due_date": str(task.due_date) if task.due_date else None
            },
            request=request,
            user_id=current_user.id
        )
        
        task_service.delete_task(db, task=task, current_user=current_user)
        
        log_business_step(
            "task_deleted_successfully",
            {
                "task_id": task_id,
                "deleted_title": task.title,
                "deleted_by": current_user.id,
                "deletion_type": "admin_deletion" if current_user.role == current_user.role.admin and task.owner_id != current_user.id else "owner_deletion"
            },
            request=request,
            user_id=current_user.id
        )
        
        return None
        
    except HTTPException:
        # Re-raise HTTP exceptions (already logged above)
        raise
    except Exception as e:
        log_business_step(
            "task_delete_failed",
            {
                "task_id": task_id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            request=request,
            user_id=current_user.id,
            level="error"
        )
        raise
