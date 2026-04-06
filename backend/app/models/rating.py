from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.db.mixins import IdPkMixin
from app.schemas.enum import RatingTarget


class Rating(Base, IdPkMixin):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    target_id: Mapped[int] = mapped_column(Integer, index=True)
    target_type: Mapped[RatingTarget] = mapped_column(Enum(RatingTarget))
    score: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "target_id", "target_type", name="uq_user_target_rating"
        ),
    )
