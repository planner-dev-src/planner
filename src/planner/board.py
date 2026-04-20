from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .task import Task


class Board:
    def __init__(self, storage_path: Path | str = "tasks.json") -> None:
        self._storage_path = Path(storage_path)
        self._tasks = self._load()

    def add_task(self, title: str) -> Task:
        task = Task(title=title)
        self._tasks.append(task)
        self._save()
        return task

    def list_tasks(self) -> list[Task]:
        return self._tasks

    def mark_task_done(self, task_id: str) -> None:
        for task in self._tasks:
            if task.id == task_id:
                task.done = True
                self._save()
                return

    def delete_task(self, task_id: str) -> None:
        self._tasks = [task for task in self._tasks if task.id != task_id]
        self._save()

    def _save(self) -> None:
        self._storage_path.write_text(
            json.dumps([asdict(task) for task in self._tasks], indent=2),
            encoding="utf-8",
        )

    def _load(self) -> list[Task]:
        if not self._storage_path.exists():
            return []

        try:
            raw_data = self._storage_path.read_text(encoding="utf-8").strip()
            if not raw_data:
                return []

            items = json.loads(raw_data)
            if not isinstance(items, list):
                return []

            return [Task(**item) for item in items]
        except (json.JSONDecodeError, TypeError, KeyError):
            return []