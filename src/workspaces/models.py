from __future__ import annotations

import uuid
from datetime import UTC, datetime

from src.extensions import db


def utcnow() -> datetime:
    return datetime.now(UTC)


class Workspace(db.Model):
    __tablename__ = "workspaces"

    id = db.Column(db.String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    name = db.Column(db.String(200), nullable=False)
    is_default = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    def __repr__(self) -> str:
        return f"<Workspace id={self.id!r} name={self.name!r}>"