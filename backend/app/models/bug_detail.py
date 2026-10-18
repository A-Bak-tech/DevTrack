
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BugDetail(Base):
    __tablename__ = "bug_details"

    issue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("issues.id", ondelete="CASCADE"),
        primary_key=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reproduction_steps: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    expected_behavior: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    actual_behavior: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    debugging_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    issue: Mapped[Issue] = relationship(
        "Issue",
        back_populates="bug_detail",
    )
