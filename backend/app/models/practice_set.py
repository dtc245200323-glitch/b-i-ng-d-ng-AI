"""Private student exercises; answer keys never leave the server before submission."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PracticeSet(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "practice_sets"
    __table_args__ = (
        ForeignKeyConstraint(
            ["student_id", "organization_id"],
            ["student_profiles.id", "student_profiles.organization_id"],
        ),
        ForeignKeyConstraint(
            ["course_id", "organization_id"],
            ["courses.id", "courses.organization_id"],
        ),
        UniqueConstraint("organization_id", "student_id", "request_key"),
    )
    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    student_id: Mapped[UUID] = mapped_column(Uuid, index=True)
    course_id: Mapped[UUID] = mapped_column(Uuid)
    request_key: Mapped[UUID] = mapped_column(Uuid)
    ai_run_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("ai_runs.id"))
    topic: Mapped[str] = mapped_column(String(200))
    level: Mapped[str] = mapped_column(String(100))
    difficulty: Mapped[str] = mapped_column(String(16))
    locale: Mapped[str] = mapped_column(String(2))
    questions: Mapped[list] = mapped_column(JSON)
    answers: Mapped[list | None] = mapped_column(JSON)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
