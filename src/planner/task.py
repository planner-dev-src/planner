from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Task:
    title: str
    id: str = field(default_factory=lambda: str(uuid4()))
    done: bool = False

    def mark_done(self) -> None:
        self.done = True

    def mark_undone(self) -> None:
        self.done = False
