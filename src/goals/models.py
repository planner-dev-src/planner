from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.planner.extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Goal(db.Model):
    __tablename__ = "goals"

    id = db.Column(db.String(32), primary_key=True, default=lambda: uuid.uuid4().hex)

    workspace_id = db.Column(
        db.String(32),
        db.ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    parent_id = db.Column(
        db.String(32),
        db.ForeignKey("goals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    kind = db.Column(db.String(32), nullable=False, default="generic")
    status = db.Column(db.String(32), nullable=False, default="planned")
    priority = db.Column(db.String(32), nullable=False, default="normal")

    version = db.Column(db.Integer, nullable=False, default=1)

    created_by = db.Column(db.String(32), nullable=False, index=True)
    updated_by = db.Column(db.String(32), nullable=False, index=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    parent = db.relationship(
        "Goal",
        remote_side=[id],
        backref=db.backref("children", lazy="select"),
        foreign_keys=[parent_id],
    )

    workspace = db.relationship("Workspace", backref=db.backref("goals", lazy="select"))

    def __repr__(self) -> str:
        return f"<Goal id={self.id} workspace_id={self.workspace_id} title={self.title!r}>"