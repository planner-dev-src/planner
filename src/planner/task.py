from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Task:
    title: str
    column_id: str
    done: bool = False
    id: str = field(default_factory=lambda: str(uuid4()))
