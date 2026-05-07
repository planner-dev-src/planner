# src/planner/services.py
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from .board import Board, Column, Task, Workspace


@lru_cache(maxsize=1)
def get_board_service() -> Board:
    return Board()


def list_workspaces() -> list[Workspace]:
    return get_board_service().list_workspaces()


def get_workspace(workspace_id: str) -> Optional[Workspace]:
    return get_board_service().get_workspace(workspace_id)


def create_workspace(name: str) -> Optional[Workspace]:
    return get_board_service().add_workspace(name=name)


def rename_workspace(workspace_id: str, name: str) -> bool:
    return get_board_service().update_workspace(workspace_id=workspace_id, name=name)


def remove_workspace(workspace_id: str) -> bool:
    return get_board_service().delete_workspace(workspace_id=workspace_id)


def list_columns(workspace_id: str) -> list[Column]:
    return get_board_service().list_columns(workspace_id=workspace_id)


def get_column(column_id: str, workspace_id: Optional[str] = None) -> Optional[Column]:
    return get_board_service().get_column(column_id=column_id, workspace_id=workspace_id)


def create_column(name: str, workspace_id: str) -> Optional[Column]:
    return get_board_service().add_column(name=name, workspace_id=workspace_id)


def rename_column(column_id: str, name: str, workspace_id: Optional[str] = None) -> bool:
    return get_board_service().update_column(
        column_id=column_id,
        name=name,
        workspace_id=workspace_id,
    )


def remove_column(column_id: str, workspace_id: Optional[str] = None) -> bool:
    return get_board_service().delete_column(
        column_id=column_id,
        workspace_id=workspace_id,
    )


def list_tasks(workspace_id: str) -> list[Task]:
    return get_board_service().list_tasks(workspace_id=workspace_id)


def list_tasks_by_column(column_id: str, workspace_id: Optional[str] = None) -> list[Task]:
    return get_board_service().get_tasks_by_column(
        column_id=column_id,
        workspace_id=workspace_id,
    )


def get_task(task_id: str, workspace_id: Optional[str] = None) -> Optional[Task]:
    return get_board_service().get_task(task_id=task_id, workspace_id=workspace_id)


def create_task(
    *,
    title: str,
    description: str,
    priority: str,
    due_date,
    column_id: str,
    workspace_id: str,
) -> Optional[Task]:
    return get_board_service().add_task(
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
        column_id=column_id,
        workspace_id=workspace_id,
    )


def update_task(
    *,
    task_id: str,
    title: str,
    description: str,
    priority: str,
    due_date,
    column_id: str,
    workspace_id: str,
) -> bool:
    return get_board_service().update_task(
        task_id=task_id,
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
        column_id=column_id,
        workspace_id=workspace_id,
    )


def remove_task(task_id: str, workspace_id: Optional[str] = None) -> bool:
    return get_board_service().delete_task(task_id=task_id, workspace_id=workspace_id)