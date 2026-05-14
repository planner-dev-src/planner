from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from sqlalchemy import select

from src.extensions import db
from .models import Goal


GOAL_STATUS_ACTIVE = "active"
GOAL_STATUS_ARCHIVED = "archived"


@dataclass
class GoalTreeNode:
    id: str
    title: str
    description: str
    status: str
    kind: str
    priority: str
    created_at: object
    children: list["GoalTreeNode"]


class GoalService:
    def get_goal(self, workspace_id: str, goal_id: str) -> Goal | None:
        stmt = (
            select(Goal)
            .where(Goal.workspace_id == workspace_id, Goal.id == goal_id)
            .limit(1)
        )
        return db.session.scalar(stmt)

    def list_root_goals(self, workspace_id: str) -> list[Goal]:
        stmt = (
            select(Goal)
            .where(
                Goal.workspace_id == workspace_id,
                Goal.parent_id.is_(None),
                Goal.status != GOAL_STATUS_ARCHIVED,
            )
            .order_by(Goal.created_at.desc(), Goal.id.desc())
        )
        return list(db.session.scalars(stmt))

    def list_archived_root_goals(self, workspace_id: str) -> list[Goal]:
        stmt = (
            select(Goal)
            .where(
                Goal.workspace_id == workspace_id,
                Goal.parent_id.is_(None),
                Goal.status == GOAL_STATUS_ARCHIVED,
            )
            .order_by(Goal.created_at.desc(), Goal.id.desc())
        )
        return list(db.session.scalars(stmt))

    def list_child_goals(self, workspace_id: str, parent_id: str) -> list[Goal]:
        stmt = (
            select(Goal)
            .where(
                Goal.workspace_id == workspace_id,
                Goal.parent_id == parent_id,
                Goal.status != GOAL_STATUS_ARCHIVED,
            )
            .order_by(Goal.created_at.asc(), Goal.id.asc())
        )
        return list(db.session.scalars(stmt))

    def list_child_goals_including_archived(
        self,
        workspace_id: str,
        parent_id: str,
    ) -> list[Goal]:
        stmt = (
            select(Goal)
            .where(
                Goal.workspace_id == workspace_id,
                Goal.parent_id == parent_id,
            )
            .order_by(Goal.created_at.asc(), Goal.id.asc())
        )
        return list(db.session.scalars(stmt))

    def _list_all(self, workspace_id: str, include_archived: bool = True) -> list[Goal]:
        stmt = select(Goal).where(Goal.workspace_id == workspace_id)
        if not include_archived:
            stmt = stmt.where(Goal.status != GOAL_STATUS_ARCHIVED)
        stmt = stmt.order_by(Goal.created_at.asc(), Goal.id.asc())
        return list(db.session.scalars(stmt))

    def list_parent_choices(
        self,
        workspace_id: str,
        exclude_goal_id: str | None = None,
    ) -> list[Goal]:
        all_goals = self._list_all(workspace_id, include_archived=False)

        if not exclude_goal_id:
            return all_goals

        descendants = self._collect_descendants(all_goals, exclude_goal_id)
        excluded = {exclude_goal_id, *descendants}
        return [g for g in all_goals if g.id not in excluded]

    def list_possible_parents(self, workspace_id: str, goal_id: str) -> list[Goal]:
        return self.list_parent_choices(workspace_id, exclude_goal_id=goal_id)

    def list_goals_for_clone_choice(self, workspace_id: str) -> list[tuple[str, str]]:
        goals = self._list_all(workspace_id, include_archived=False)
        return [(g.id, g.title) for g in goals]

    def create_goal(
        self,
        workspace_id: str,
        title: str,
        description: str,
        kind: str,
        status: str,
        priority: str,
        parent_id: str | None,
        actor_user_id: str,
    ) -> Goal:
        workspace_id = (workspace_id or "").strip()
        title = (title or "").strip()
        description = (description or "").strip()
        kind = (kind or "").strip() or "goal"
        status = (status or "").strip() or "planned"
        priority = (priority or "").strip() or "medium"
        parent_id = (parent_id or None) or None

        if not workspace_id:
            raise ValueError("workspace_id обязателен.")

        if not title:
            raise ValueError("Название цели обязательно.")

        if parent_id is not None:
            parent = self.get_goal(workspace_id, parent_id)
            if parent is None:
                raise ValueError("Родительская цель не найдена.")

        goal = Goal(
            workspace_id=workspace_id,
            title=title,
            description=description or None,
            kind=kind,
            status=status,
            priority=priority,
            parent_id=parent_id,
            created_by=actor_user_id,
            updated_by=actor_user_id,
        )
        db.session.add(goal)
        db.session.commit()
        return goal

    def update_goal(
        self,
        workspace_id: str,
        goal_id: str,
        title: str,
        description: str,
        kind: str,
        status: str,
        priority: str,
        parent_id: str | None,
        actor_user_id: str,
    ) -> Goal:
        goal = self.get_goal(workspace_id, goal_id)
        if goal is None:
            raise ValueError("Цель не найдена.")

        title = (title or "").strip()
        description = (description or "").strip()
        kind = (kind or "").strip() or goal.kind
        status = (status or "").strip() or goal.status
        priority = (priority or "").strip() or goal.priority
        parent_id = (parent_id or None) or None

        if not title:
            raise ValueError("Название цели обязательно.")

        if parent_id == goal.id:
            raise ValueError("Нельзя сделать цель родителем самой себя.")

        if parent_id is not None:
            possible_parents = {
                item.id for item in self.list_possible_parents(workspace_id, goal.id)
            }
            if parent_id not in possible_parents:
                raise ValueError("Нельзя перенести цель в выбранного родителя.")

        goal.title = title
        goal.description = description or None
        goal.kind = kind
        goal.status = status
        goal.priority = priority
        goal.parent_id = parent_id
        goal.updated_by = actor_user_id

        db.session.add(goal)
        db.session.commit()
        return goal

    def _collect_descendants(
        self,
        goals: Iterable[Goal],
        root_id: str,
    ) -> set[str]:
        by_parent: dict[Optional[str], list[Goal]] = {}
        for g in goals:
            by_parent.setdefault(g.parent_id, []).append(g)

        result: set[str] = set()
        stack = [root_id]

        while stack:
            current = stack.pop()
            for child in by_parent.get(current, []):
                if child.id not in result:
                    result.add(child.id)
                    stack.append(child.id)

        return result

    def build_goal_tree(self, workspace_id: str, root_goal_id: str) -> GoalTreeNode:
        all_goals = self._list_all(workspace_id, include_archived=True)
        by_id = {g.id: g for g in all_goals}

        root = by_id.get(root_goal_id)
        if root is None:
            raise ValueError("Цель не найдена.")

        by_parent: dict[Optional[str], list[Goal]] = {}
        for g in all_goals:
            by_parent.setdefault(g.parent_id, []).append(g)

        def build_node(goal: Goal) -> GoalTreeNode:
            children_nodes = [build_node(child) for child in by_parent.get(goal.id, [])]
            return GoalTreeNode(
                id=goal.id,
                title=goal.title,
                description=goal.description or "",
                status=goal.status,
                kind=goal.kind,
                priority=goal.priority,
                created_at=goal.created_at,
                children=children_nodes,
            )

        return build_node(root)

    def clone_goal_tree(
        self,
        workspace_id: str,
        source_goal_id: str,
        new_root_title: str,
        actor_user_id: str,
    ) -> Goal:
        source_goal = self.get_goal(workspace_id, source_goal_id)
        if source_goal is None:
            raise ValueError("Исходная цель не найдена.")

        tree_root = self.build_goal_tree(workspace_id, source_goal_id)
        all_goals = self._list_all(workspace_id, include_archived=True)
        by_id = {g.id: g for g in all_goals}

        new_root_title = (new_root_title or "").strip()
        if not new_root_title:
            raise ValueError("Название новой корневой копии обязательно.")

        def clone_node(node: GoalTreeNode, new_parent_id: str | None) -> Goal:
            original = by_id[node.id]
            title = new_root_title if node.id == tree_root.id else node.title

            cloned = Goal(
                workspace_id=workspace_id,
                title=title,
                description=node.description or None,
                kind=original.kind,
                status=original.status,
                priority=original.priority,
                parent_id=new_parent_id,
                created_by=actor_user_id,
                updated_by=actor_user_id,
            )
            db.session.add(cloned)
            db.session.flush()

            for child in node.children:
                clone_node(child, cloned.id)

            return cloned

        cloned_root = clone_node(tree_root, None)
        db.session.commit()
        return cloned_root

    def attach_existing_goal(
        self,
        workspace_id: str,
        parent_goal_id: str,
        child_goal_id: str,
        actor_user_id: str,
    ) -> None:
        parent = self.get_goal(workspace_id, parent_goal_id)
        child = self.get_goal(workspace_id, child_goal_id)

        if parent is None or child is None:
            raise ValueError("Цель не найдена.")

        if parent.id == child.id:
            raise ValueError("Нельзя встроить цель в саму себя.")

        all_goals = self._list_all(workspace_id, include_archived=False)
        descendants = self._collect_descendants(all_goals, child.id)
        if parent.id in descendants:
            raise ValueError("Нельзя встроить цель в своё поддерево.")

        child.parent_id = parent.id
        child.updated_by = actor_user_id
        db.session.add(child)
        db.session.commit()

    def move_goal(
        self,
        workspace_id: str,
        goal_id: str,
        new_parent_id: str | None,
        actor_user_id: str,
    ) -> None:
        goal = self.get_goal(workspace_id, goal_id)
        if goal is None:
            raise ValueError("Цель не найдена.")

        if new_parent_id == "":
            new_parent_id = None

        if new_parent_id == goal.id:
            raise ValueError("Нельзя сделать цель родителем самой себя.")

        if new_parent_id is not None:
            parent = self.get_goal(workspace_id, new_parent_id)
            if parent is None:
                raise ValueError("Новый родитель не найден.")

            all_goals = self._list_all(workspace_id, include_archived=False)
            descendants = self._collect_descendants(all_goals, goal.id)
            if new_parent_id in descendants:
                raise ValueError("Нельзя перенести цель внутрь собственного поддерева.")

        goal.parent_id = new_parent_id
        goal.updated_by = actor_user_id
        db.session.add(goal)
        db.session.commit()

    def archive_goal(
        self,
        workspace_id: str,
        goal_id: str,
        actor_user_id: str,
    ) -> None:
        goal = self.get_goal(workspace_id, goal_id)
        if goal is None:
            raise ValueError("Цель не найдена.")

        if goal.status == GOAL_STATUS_ARCHIVED:
            raise ValueError("Цель уже в архиве.")

        goal.status = GOAL_STATUS_ARCHIVED
        goal.updated_by = actor_user_id
        db.session.add(goal)
        db.session.commit()

    def restore_goal(
        self,
        workspace_id: str,
        goal_id: str,
        actor_user_id: str,
    ) -> None:
        goal = self.get_goal(workspace_id, goal_id)
        if goal is None:
            raise ValueError("Цель не найдена.")

        if goal.status != GOAL_STATUS_ARCHIVED:
            raise ValueError("Цель уже активна.")

        if goal.parent_id is not None:
            parent = self.get_goal(workspace_id, goal.parent_id)
            if parent is None:
                raise ValueError("Невозможно восстановить цель: родитель не найден.")
            if parent.status == GOAL_STATUS_ARCHIVED:
                raise ValueError("Нельзя восстановить цель, пока её родитель в архиве.")

        goal.status = GOAL_STATUS_ACTIVE
        goal.updated_by = actor_user_id
        db.session.add(goal)
        db.session.commit()

    def can_delete_goal(self, workspace_id: str, goal_id: str) -> dict:
        goal = self.get_goal(workspace_id, goal_id)
        if goal is None:
            raise ValueError("Цель не найдена.")

        children = self.list_child_goals_including_archived(workspace_id, goal_id)
        all_goals = self._list_all(workspace_id, include_archived=True)
        descendants = self._collect_descendants(all_goals, goal_id)

        return {
            "has_children": bool(children),
            "children_count": len(children),
            "descendants_count": len(descendants),
            "is_archived": goal.status == GOAL_STATUS_ARCHIVED,
        }

    def _delete_goal_subtree(self, workspace_id: str, goal_id: str) -> None:
        children = self.list_child_goals_including_archived(workspace_id, goal_id)
        for child in children:
            self._delete_goal_subtree(workspace_id, child.id)

        goal = self.get_goal(workspace_id, goal_id)
        if goal is not None:
            db.session.delete(goal)

    def delete_goal_with_policy(
        self,
        workspace_id: str,
        goal_id: str,
        delete_descendants: bool,
        actor_user_id: str,
    ) -> None:
        goal = self.get_goal(workspace_id, goal_id)
        if goal is None:
            raise ValueError("Цель не найдена.")

        if goal.status != GOAL_STATUS_ARCHIVED:
            raise ValueError("Удалять можно только архивную цель.")

        children = self.list_child_goals_including_archived(workspace_id, goal_id)
        if children and not delete_descendants:
            raise ValueError(
                "Для удаления этой цели нужно подтвердить удаление вложенных элементов."
            )

        if children and delete_descendants:
            self._delete_goal_subtree(workspace_id, goal_id)
            db.session.commit()
            return

        db.session.delete(goal)
        db.session.commit()