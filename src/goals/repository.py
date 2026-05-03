from __future__ import annotations

from sqlalchemy import select

from src.planner.extensions import db
from .models import Goal


class GoalRepository:
    def list_by_workspace(self, workspace_id: str) -> list[Goal]:
        stmt = (
            select(Goal)
            .where(Goal.workspace_id == workspace_id)
            .order_by(Goal.created_at.asc(), Goal.id.asc())
        )
        return list(db.session.scalars(stmt))

    def list_possible_parents(
        self,
        workspace_id: str,
        exclude_goal_id: str | None = None,
    ) -> list[Goal]:
        stmt = (
            select(Goal)
            .where(Goal.workspace_id == workspace_id)
            .order_by(Goal.title.asc(), Goal.created_at.asc())
        )

        if exclude_goal_id:
            stmt = stmt.where(Goal.id != exclude_goal_id)

        return list(db.session.scalars(stmt))

    def get_by_id(self, workspace_id: str, goal_id: str) -> Goal | None:
        stmt = select(Goal).where(
            Goal.workspace_id == workspace_id,
            Goal.id == goal_id,
        )
        return db.session.scalar(stmt)

    def add(self, goal: Goal) -> Goal:
        db.session.add(goal)
        return goal

    def delete(self, goal: Goal) -> None:
        db.session.delete(goal)