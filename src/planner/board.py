import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from planner.task import Task


@dataclass
class Board:
    tasks: list[Task] = field(default_factory=list)
    storage_path: Path = field(default_factory=lambda: Path("tasks.json"))

    def __post_init__(self) -> None:
        self._load()

    def _load(self) -> None:
        if not self.storage_path.exists():
            return

        try:
            raw_text = self.storage_path.read_text(encoding="utf-8").strip()
            if not raw_text:
                self.tasks = []
                return

            data = json.loads(raw_text)

            if not isinstance(data, list):
                raise ValueError("tasks.json must contain a list")

            loaded_tasks: list[Task] = []
            for item in data:
                if not isinstance(item, dict):
                    raise ValueError("Each task must be an object")

                loaded_tasks.append(Task(**item))

            self.tasks = loaded_tasks

        except (json.JSONDecodeError, ValueError, TypeError):
            backup_path = self.storage_path.with_suffix(".broken.json")
            self.storage_path.rename(backup_path)
            self.tasks = []

    def _save(self) -> None:
        data = [asdict(task) for task in self.tasks]
        self.storage_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add_task(self, title: str) -> Task:
        task = Task(title=title)
        self.tasks.append(task)
        self._save()
        return task

    def list_tasks(self) -> list[Task]:
        return self.tasks

    def get_task(self, task_id: str) -> Task | None:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def mark_task_done(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if task is None:
            return False

        task.mark_done()
        self._save()
        return True

    def remove_task(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if task is None:
            return False

        self.tasks.remove(task)
        self._save()
        return True