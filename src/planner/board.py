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
    is_done_column: bool = False
    id: str = field(default_factory=lambda: str(uuid4()))


class Board:
    def __init__(self, storage_path: Path | str = "board.json") -> None:
        self._storage_path = Path(storage_path)
        self._columns: list[Column] = []
        self._tasks: list[Task] = []
        self._load()

        if not self._columns:
            self.add_column("Inbox")

        self._ensure_done_column()
        self._normalize_column_positions()
        self._sync_task_done_flags()

    def list_columns(self) -> list[Column]:
        return sorted(
            self._columns,
            key=lambda column: (column.is_done_column, column.position),
        )

    def list_tasks(self) -> list[Task]:
        return list(self._tasks)

    def get_tasks_by_column(self, column_id: str) -> list[Task]:
        return [task for task in self._tasks if task.column_id == column_id]

    def get_column(self, column_id: str) -> Column | None:
        for column in self._columns:
            if column.id == column_id:
                return column
        return None

    def get_done_column(self) -> Column | None:
        for column in self._columns:
            if column.is_done_column:
                return column
        return None

    def add_column(self, name: str) -> Column | None:
        cleaned_name = name.strip()
        if not cleaned_name:
            return None

        regular_columns = [column for column in self._columns if not column.is_done_column]
        column = Column(name=cleaned_name, position=len(regular_columns))
        self._columns.append(column)
        self._normalize_column_positions()
        self._save()
        return column

    def update_column(self, column_id: str, new_name: str) -> bool:
        cleaned_name = new_name.strip()
        if not cleaned_name:
            return False

        for column in self._columns:
            if column.id == column_id:
                if column.is_done_column:
                    return False
                column.name = cleaned_name
                self._save()
                return True
        return False

    def is_column_empty(self, column_id: str) -> bool:
        return not any(task.column_id == column_id for task in self._tasks)

    def delete_column(self, column_id: str) -> bool:
        column = self.get_column(column_id)
        if column is None:
            return False

        if column.is_done_column:
            return False

        if not self.is_column_empty(column_id):
            return False

        original_count = len(self._columns)
        self._columns = [item for item in self._columns if item.id != column_id]

        if len(self._columns) == original_count:
            return False

        self._normalize_column_positions()
        self._save()
        return True

    def add_task(self, title: str, column_id: str) -> Task | None:
        cleaned_title = title.strip()
        if not cleaned_title:
            return None

        column = self.get_column(column_id)
        if column is None or column.is_done_column:
            return None

        task = Task(title=cleaned_title, column_id=column_id, done=False)
        self._tasks.append(task)
        self._save()
        return task

    def get_task(self, task_id: str) -> Task | None:
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def update_task(self, task_id: str, new_title: str, new_column_id: str) -> bool:
        cleaned_title = new_title.strip()
        if not cleaned_title:
            return False

        column = self.get_column(new_column_id)
        if column is None:
            return False

        for task in self._tasks:
            if task.id == task_id:
                task.title = cleaned_title
                task.column_id = new_column_id
                task.done = column.is_done_column
                self._save()
                return True
        return False

    def delete_task(self, task_id: str) -> bool:
        original_count = len(self._tasks)
        self._tasks = [task for task in self._tasks if task.id != task_id]

        if len(self._tasks) == original_count:
            return False

        self._save()
        return True

    def move_task_left(self, task_id: str) -> bool:
        ordered_columns = self.list_columns()
        task = self.get_task(task_id)
        if task is None:
            return False

        current_index = self._find_column_index(task.column_id, ordered_columns)
        if current_index is None or current_index == 0:
            return False

        new_column = ordered_columns[current_index - 1]
        task.column_id = new_column.id
        task.done = new_column.is_done_column
        self._save()
        return True

    def move_task_right(self, task_id: str) -> bool:
        ordered_columns = self.list_columns()
        task = self.get_task(task_id)
        if task is None:
            return False

        current_index = self._find_column_index(task.column_id, ordered_columns)
        if current_index is None or current_index >= len(ordered_columns) - 1:
            return False

        new_column = ordered_columns[current_index + 1]
        task.column_id = new_column.id
        task.done = new_column.is_done_column
        self._save()
        return True

    def move_task_to_done(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        done_column = self.get_done_column()

        if task is None or done_column is None:
            return False

        task.column_id = done_column.id
        task.done = True
        self._save()
        return True

    def _find_column_index(self, column_id: str, columns: list[Column]) -> int | None:
        for index, column in enumerate(columns):
            if column.id == column_id:
                return index
        return None

    def _ensure_done_column(self) -> None:
        done_column = self.get_done_column()
        if done_column is not None:
            return

        for column in self._columns:
            normalized_name = column.name.strip().casefold()
            if normalized_name in {"done", "сделано"}:
                column.is_done_column = True
                self._save()
                return

        self._columns.append(
            Column(
                name="Сделано",
                position=len([column for column in self._columns if not column.is_done_column]),
                is_done_column=True,
            )
        )
        self._save()

    def _normalize_column_positions(self) -> None:
        regular_columns = sorted(
            [column for column in self._columns if not column.is_done_column],
            key=lambda column: column.position,
        )

        for index, column in enumerate(regular_columns):
            column.position = index

        done_column = self.get_done_column()
        if done_column is not None:
            done_column.position = len(regular_columns)

    def _sync_task_done_flags(self) -> None:
        changed = False
        for task in self._tasks:
            column = self.get_column(task.column_id)
            should_be_done = bool(column and column.is_done_column)
            if task.done != should_be_done:
                task.done = should_be_done
                changed = True

        if changed:
            self._save()

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

            self._columns = [
                Column(
                    name=item["name"],
                    position=item["position"],
                    is_done_column=item.get("is_done_column", False),
                    id=item["id"],
                )
                for item in columns_data
            ]
            self._tasks = [Task(**item) for item in tasks_data]
        except (json.JSONDecodeError, TypeError, KeyError):
            self._columns = []
            self._tasks = []