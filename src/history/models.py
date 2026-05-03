from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.planner.extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ChangeEvent(db.Model):
    __tablename__ = "change_events"

    id = db.Column(db.String(32), primary_key=True, default=lambda: uuid.uuid4().hex)

    workspace_id = db.Column(
        db.String(32),
        db.ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    aggregate_type = db.Column(db.String(64), nullable=False, index=True)
    aggregate_id = db.Column(db.String(32), nullable=False, index=True)

    event_type = db.Column(db.String(64), nullable=False, index=True)
    actor_user_id = db.Column(db.String(32), nullable=False, index=True)

    version = db.Column(db.Integer, nullable=False)
    payload = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    workspace = db.relationship(
        "Workspace",
        backref=db.backref("change_events", lazy="select"),
    )

    def __repr__(self) -> str:
        return (
            f"<ChangeEvent id={self.id} workspace_id={self.workspace_id} "
            f"aggregate_type={self.aggregate_type} aggregate_id={self.aggregate_id} "
            f"event_type={self.event_type}>"
        )