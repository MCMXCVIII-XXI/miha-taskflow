from datetime import datetime

from pydantic import BaseModel, Field


class CommentRead(BaseModel):
    id: int = Field(description="Comment ID")
    task_id: int = Field(description="Task ID")
    user_id: int = Field(description="User ID")
    content: str = Field(description="Comment content")
    parent_id: int | None = Field(description="Parent comment ID")
    created_at: datetime = Field(description="Comment creation time")
    updated_at: datetime | None = Field(description="Comment update time")


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=255, description="Comment content")
    parent_id: int | None = Field(None, description="Parent comment ID")


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=255, description="Comment content")
