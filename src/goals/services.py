from __future__ import annotations

from datetime import datetime, timezone

from src.planner.extensions import db
from src.history.models import ChangeEvent
from src.history.repository import ChangeEventRepository
from .models import Goal
from .repository import GoalRepository

ALLOWED_KINDS = {"generic", "outcome", "milestone"}
ALLOWED_STATUSES = {"planned", "active", "done", "archived"}
ALLOWED_PRIORITIES = {"low", "normal", "high"}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GoalService:
    def __init__(
        self,
        repository: GoalRepository | None = None,
        change_event_repository: ChangeEventRepository | None = None,
    ) -> None:
        self.repository = repository or GoalRepository()
        self.change_event_repository = change_event_repository or ChangeEventRepository()

    def list_goals(self, workspace_id: str) -> list[Goal]:
        return self.repository.list_by_workspace(workspace_id)

    def get_goal(self, workspace_id: str, goal_id: str) -> Goal | None:
        return self.repository.get_by_id(workspace_id, goal_id)

    def list_parent_choices(
        self,
        workspace_id: str,
        exclude_goal_id: str | None = None,
    ) -> list[Goal]:
        return self.repository.list_possible_parents(
            workspace_id=workspace_id,
            exclude_goal_id=exclude_goal_id,
        )

    def create_goal(
        self,
        *,
        workspace_id: str,
        title: str,
        description: str | None,
        kind: str,
        status: str,
        priority: str,
        parent_id: str | None,
        actor_user_id: str,
    ) -> Goal:
        workspace_id = (workspace_id or "").strip()
        title = (title or "").strip()
        description = (description or "").strip()

        if not workspace_id:
            raise ValueError("workspace_id is required")

        if not actor_user_id:
            raise ValueError("actor_user_id is required")

        if not title:
            raise ValueError("title is required")

        kind = self._normalize_kind(kind)
        status = self._normalize_status(status)
        priority = self._normalize_priority(priority)
        normalized_parent_id = self._normalize_parent_id(parent_id)

        if normalized_parent_id:
            parent = self.repository.get_by_id(workspace_id, normalized_parent_id)
            if parent is None:
                raise ValueError("parent goal not found")

        now = utcnow()

        goal = Goal(
            workspace_id=workspace_id,
            title=title,
            description=description or None,
            kind=kind,
            status=status,
            priority=priority,
            parent_id=normalized_parent_id,
            created_by=actor_user_id,
            updated_by=actor_user_id,
            created_at=now,
            updated_at=now,
            version=1,
        )

        self.repository.add(goal)
        self._add_change_event(
            workspace_id=workspace_id,
            aggregate_type="goal",
            aggregate_id=goal.id,
            event_type="goal.created",
            actor_user_id=actor_user_id,
            version=goal.version,
            payload={
                "title": goal.title,
                "description": goal.description,
                "kind": goal.kind,
                "status": goal.status,
                "priority": goal.priority,
                "parent_id": goal.parent_id,
            },
        )
        db.session.commit()
        return goal

    def update_goal(
        self,
        *,
        workspace_id: str,
        goal_id: str,
        title: str,
        description: str | None,
        kind: str,
        status: str,
        priority: str,
        parent_id: str | None,
        actor_user_id: str,
    ) -> Goal:
        workspace_id = (workspace_id or "").strip()
        goal_id = (goal_id or "").strip()
        title = (title or "").strip()
        description = (description or "").strip()

        if not workspace_id:
            raise ValueError("workspace_id is required")

        if not goal_id:
            raise ValueError("goal_id is required")

        if not actor_user_id:
            raise ValueError("actor_user_id is required")

        if not title:
            raise ValueError("title is required")

        goal = self.repository.get_by_id(workspace_id, goal_id)
        if goal is None:
            raise ValueError("goal not found")

        kind = self._normalize_kind(kind)
        status = self._normalize_status(status)
        priority = self._normalize_priority(priority)
        normalized_parent_id = self._normalize_parent_id(parent_id)

        if normalized_parent_id == goal.id:
            raise ValueError("goal cannot be parent of itself")

        if normalized_parent_id:
            parent = self.repository.get_by_id(workspace_id, normalized_parent_id)
            if parent is None:
                raise ValueError("parent goal not found")

        previous_state = {
            "title": goal.title,
            "description": goal.description,
            "kind": goal.kind,
            "status": goal.status,
            "priority": goal.priority,
            "parent_id": goal.parent_id,
            "version": goal.version,
        }

        goal.title = title
        goal.description = description or None
        goal.kind = kind
        goal.status = status
        goal.priority = priority
        goal.parent_id = normalized_parent_id
        goal.updated_by = actor_user_id
        goal.updated_at = utcnow()
        goal.version = (goal.version or 0) + 1

        self._add_change_event(
            workspace_id=workspace_id,
            aggregate_type="goal",
            aggregate_id=goal.id,
            event_type="goal.updated",
            actor_user_id=actor_user_id,
            version=goal.version,
            payload={
                "before": previous_state,
                "after": {
                    "title": goal.title,
                    "description": goal.description,
                    "kind": goal.kind,
                    "status": goal.status,
                    "priority": goal.priority,
                    "parent_id": goal.parent_id,
                    "version": goal.version,
                },
            },
        )
        db.session.commit()
        return goal

    def delete_goal(
        self,
        *,
        workspace_id: str,
        goal_id: str,
        actor_user_id: str,
    ) -> None:
        workspace_id = (workspace_id or "").strip()
        goal_id = (goal_id or "").strip()

        if not workspace_id:
            raise ValueError("workspace_id is required")

        if not goal_id:
            raise ValueError("goal_id is required")

        if not actor_user_id:
            raise ValueError("actor_user_id is required")

        goal = self.repository.get_by_id(workspace_id, goal_id)
        if goal is None:
            raise ValueError("goal not found")

        event_version = (goal.version or 0) + 1

        self._add_change_event(
            workspace_id=workspace_id,
            aggregate_type="goal",
            aggregate_id=goal.id,
            event_type="goal.deleted",
            actor_user_id=actor_user_id,
            version=event_version,
            payload={
                "title": goal.title,
                "description": goal.description,
                "kind": goal.kind,
                "status": goal.status,
                "priority": goal.priority,
                "parent_id": goal.parent_id,
                "deleted_goal_version": goal.version,
            },
        )

        self.repository.delete(goal)
        db.session.commit()

    def _add_change_event(
        self,
        *,
        workspace_id: str,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        actor_user_id: str,
        version: int,
        payload: dict | None,
    ) -> ChangeEvent:
        event = ChangeEvent(
            workspace_id=workspace_id,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            actor_user_id=actor_user_id,
            version=version,
            payload=payload,
        )
        return self.change_event_repository.add(event)

    def _normalize_kind(self, kind: str | None) -> str:
        kind = (kind or "").strip()
        return kind if kind in ALLOWED_KINDS else "generic"

    def _normalize_status(self, status: str | None) -> str:
        status = (status or "").strip()
        return status if status in ALLOWED_STATUSES else "planned"

    def _normalize_priority(self, priority: str | None) -> str:
        priority = (priority or "").strip()
        return priority if priority in ALLOWED_PRIORITIES else "normal"

    def _normalize_parent_id(self, parent_id: str | None) -> str | None:
        value = (parent_id or "").strip()
        return value or None