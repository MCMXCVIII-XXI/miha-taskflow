from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .enum import RatingTarget


class RatingCreate(BaseModel):
    score: int = Field(ge=1, le=10, description="Rating score from 1 to 10")


class RatingRead(BaseModel):
    id: int = Field(description="Rating ID")
    user_id: int = Field(description="User ID")
    target_id: int = Field(description="Target ID")
    target_type: RatingTarget = Field(description="Target type")
    score: int = Field(description="Rating score")
    created_at: datetime = Field(description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class RatingStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    target_id: int = Field(description="Target ID")
    average_score: float = Field(description="Average score")
    count: int = Field(description="Number of ratings")
