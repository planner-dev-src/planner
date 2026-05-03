from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


@dataclass
class ContentItem:
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    body: str = ""
    category: str = ""
    visibility: str = "private"   # позже: system/private/workspace
    workspace_id: str | None = None
    author_user_id: str | None = None
    version: int = 1
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)