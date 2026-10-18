
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Issue(Base):
    __tablename__ = "issues"

    
    __table_args__ = (
        CheckConstraint(
            "issue_type IN ('task', 'bug')",
            name="ck_issues_type",
        ),
        CheckConstraint(
            "status IN ('todo', 'in_progress', 'in_review', 'done')",
            name="ck_issues_status",
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'critical')",
            name="ck_issues_priority",
        ),
        CheckConstraint(
            "revision >= 1",
            name="ck_issues_revision_positive",
        ),
        CheckConstraint(
            "length(btrim(title)) > 0",
            name="ck_issues_title_not_blank",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    issue_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="todo",
        server_default="todo",
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(10),
        default="medium",
        server_default="medium",
        nullable=False,
    )

    revision: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    project: Mapped[Project] = relationship(
        "Project",
        back_populates="issues",
    )
    
    
    bug_detail: Mapped[BugDetail | None] = relationship(
        "BugDetail",
        back_populates="issue",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
    )

