from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enum import JoinRequestStatus


class JoinRequestRead(BaseModel):
    id: int = Field(description="The unique identifier of the join request")
    user_id: int = Field(description="The ID of the user who made the join request")
    group_id: int = Field(description="The ID of the group the user is joining")
    task_id: int | None = Field(
        description="The ID of the task the user is joining, if any"
    )
    status: JoinRequestStatus = Field(description="The status of the join request")
    created_at: datetime = Field(
        description="The timestamp when the join request was created"
    )

    model_config = ConfigDict(from_attributes=True)
