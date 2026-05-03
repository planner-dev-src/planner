from __future__ import annotations

from src.planner.extensions import db
from .models import ChangeEvent


class ChangeEventRepository:
    def add(self, event: ChangeEvent) -> ChangeEvent:
        db.session.add(event)
        return event