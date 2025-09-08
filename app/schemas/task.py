from datetime import datetime, date
from pydantic import BaseModel, ConfigDict
from typing import List

class TaskBase(BaseModel):
    title: str
    description: str | None = None
    due_date: date | None = None

    model_config = ConfigDict(from_attributes=True)

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    due_date: date | None = None
    status: str | None = None  # pending | in_progress | done

    model_config = ConfigDict(from_attributes=True)

class TaskRead(BaseModel):
    id: int
    title: str
    description: str | None
    status: str
    due_date: date | None
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaginatedTasks(BaseModel):
    total: int
    items: List[TaskRead]

    model_config = ConfigDict(from_attributes=True)
