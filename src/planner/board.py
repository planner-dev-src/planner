from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from uuid import uuid4

from .task import Task


@dataclass
class Column:
    name: str
    position: int
    id: str = field(default_factory=lambda: str(uuid4()))


class Board:
    def __init__(self, storage_path: Path | str = "board.json") -> None:
        self._storage_path = Path(storage_path)
        self._columns: list[Column] = []
        self._tasks: list[Task] = []
        self._load()

        if not self._columns:
            self.add_column("Inbox")

    def list_columns(self) -> list[Column]:
        return sorted(self._columns, key=lambda column: column.position)

    def list_tasks(self) -> list[Task]:
        return self._tasks

    def get_tasks_by_column(self, column_id: str) -> list[Task]:
        return [task for task in self._tasks if task.column_id == column_id]

    def get_column(self, column_id: str) -> Column | None:
        for column in self._columns:
            if column.id == column_id:
                return column
        return None

    def add_column(self, name: str) -> Column:
        column = Column(name=name, position=len(self._columns))
        self._columns.append(column)
        self._save()
        return column

    def update_column(self, column_id: str, new_name: str) -> bool:
        for column in self._columns:
            if column.id == column_id:
                column.name = new_name
                self._save()
                return True
        return False

    def add_task(self, title: str, column_id: str) -> Task | None:
        if self.get_column(column_id) is None:
            return None

        task = Task(title=title, column_id=column_id)
        self._tasks.append(task)
        self._save()
        return task

    def get_task(self, task_id: str) -> Task | None:
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def update_task(self, task_id: str, new_title: str, new_column_id: str) -> bool:
        if self.get_column(new_column_id) is None:
            return False

        for task in self._tasks:
            if task.id == task_id:
                task.title = new_title
                task.column_id = new_column_id
                self._save()
                return True
        return False

    def delete_task(self, task_id: str) -> None:
        self._tasks = [task for task in self._tasks if task.id != task_id]
        self._save()

    def move_task_left(self, task_id: str) -> None:
        ordered_columns = self.list_columns()
        task = self.get_task(task_id)
        if task is None:
            return

        current_index = self._find_column_index(task.column_id, ordered_columns)
        if current_index is None or current_index == 0:
            return

        task.column_id = ordered_columns[current_index - 1].id
        self._save()

    def move_task_right(self, task_id: str) -> None:
        ordered_columns = self.list_columns()
        task = self.get_task(task_id)
        if task is None:
            return

        current_index = self._find_column_index(task.column_id, ordered_columns)
        if current_index is None or current_index >= len(ordered_columns) - 1:
            return

        task.column_id = ordered_columns[current_index + 1].id
        self._save()

    def move_task_to_done(self, task_id: str) -> None:
        ordered_columns = self.list_columns()
        task = self.get_task(task_id)

        if task is None or not ordered_columns:
            return

        task.column_id = ordered_columns[-1].id
        self._save()

    def _find_column_index(self, column_id: str, columns: list[Column]) -> int | None:
        for index, column in enumerate(columns):
            if column.id == column_id:
                return index
        return None

    def _save(self) -> None:
        payload = {
            "columns": [asdict(column) for column in self._columns],
            "tasks": [asdict(task) for task in self._tasks],
        }
        self._storage_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _load(self) -> None:
        if not self._storage_path.exists():
            self._columns = []
            self._tasks = []
            return

        try:
            raw_data = self._storage_path.read_text(encoding="utf-8").strip()
            if not raw_data:
                self._columns = []
                self._tasks = []
                return

            data = json.loads(raw_data)

            columns_data = data.get("columns", [])
            tasks_data = data.get("tasks", [])

            self._columns = [Column(**item) for item in columns_data]
            self._tasks = [Task(**item) for item in tasks_data]
        except (json.JSONDecodeError, TypeError, KeyError):
            self._columns = []
            self._tasks = []