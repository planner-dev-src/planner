from dataclasses import dataclass, field

from planner.task import Task


@dataclass
class Board:
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, title: str) -> Task:
        task = Task(title=title)
        self.tasks.append(task)
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
        return True

    def remove_task(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if task is None:
            return False

        self.tasks.remove(task)
        return True