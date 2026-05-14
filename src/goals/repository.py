from __future__ import annotations

from typing import Iterable, List, Optional

from sqlalchemy import select

from src.extensions import db
from .models import Goal


class GoalRepository:
    @classmethod
    def get(cls, workspace_id: str, goal_id: str) -> Optional[Goal]:
        stmt = (
            select(Goal)
            .where(Goal.workspace_id == workspace_id, Goal.id == goal_id)
            .limit(1)
        )
        return db.session.scalar(stmt)

    @classmethod
    def list_root(cls, workspace_id: str, archived: bool = False) -> List[Goal]:
        if archived:
            status_filter = Goal.status == "archived"
        else:
            status_filter = Goal.status != "archived"

        stmt = (
            select(Goal)
            .where(
                Goal.workspace_id == workspace_id,
                Goal.parent_id.is_(None),
                status_filter,
            )
            .order_by(Goal.created_at.desc(), Goal.id.desc())
        )
        return list(db.session.scalars(stmt))

    @classmethod
    def list_children(cls, workspace_id: str, parent_id: str) -> List[Goal]:
        stmt = (
            select(Goal)
            .where(
                Goal.workspace_id == workspace_id,
                Goal.parent_id == parent_id,
            )
            .order_by(Goal.created_at.asc(), Goal.id.asc())
        )
        return list(db.session.scalars(stmt))

    @classmethod
    def list_for_workspace(cls, workspace_id: str) -> List[Goal]:
        stmt = (
            select(Goal)
            .where(Goal.workspace_id == workspace_id)
            .order_by(Goal.created_at.asc(), Goal.id.asc())
        )
        return list(db.session.scalars(stmt))

    @classmethod
    def list_all(cls, workspace_id: str, include_archived: bool = True) -> List[Goal]:
        stmt = select(Goal).where(Goal.workspace_id == workspace_id)

        if not include_archived:
            stmt = stmt.where(Goal.status != "archived")

        stmt = stmt.order_by(Goal.created_at.asc(), Goal.id.asc())
        return list(db.session.scalars(stmt))

    @classmethod
    def list_many(cls, workspace_id: str, ids: Iterable[str]) -> List[Goal]:
        ids = list(ids)
        if not ids:
            return []

        stmt = (
            select(Goal)
            .where(Goal.workspace_id == workspace_id, Goal.id.in_(ids))
            .order_by(Goal.created_at.asc(), Goal.id.asc())
        )
        return list(db.session.scalars(stmt))

    @classmethod
    def create(
        cls,
        workspace_id: str,
        title: str,
        description: str = "",
        kind: str = "generic",
        status: str = "planned",
        priority: str = "normal",
        parent_id: Optional[str] = None,
        created_by: str = "system",
    ) -> Goal:
        goal = Goal(
            workspace_id=workspace_id,
            title=title,
            description=description or None,
            kind=kind,
            status=status,
            priority=priority,
            parent_id=parent_id,
            created_by=created_by,
            updated_by=created_by,
        )
        db.session.add(goal)
        db.session.flush()
        return goal

    @classmethod
    def delete(cls, workspace_id: str, goal_id: str) -> None:
        goal = cls.get(workspace_id, goal_id)
        if goal is None:
            return
        db.session.delete(goal)

    @classmethod
    def save(cls, goal: Goal) -> Goal:
        db.session.add(goal)
        return goal